"""
PowerShell identifier renaming transformer.
"""
import re
from typing import Dict, Optional

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class RenameIdentifiers:
    """Transformer that renames variables and functions in PowerShell scripts."""
    
    def __init__(self):
        self.variable_mapping: Dict[str, str] = {}
        self.function_mapping: Dict[str, str] = {}
        self.map_tracker: Dict[str, Dict] = {"Functions": {}, "Variables": {}}
        
        # Reserved PowerShell keywords/automatic variables and .NET types (case-insensitive)
        self.reserved_keywords = {
            'begin', 'break', 'catch', 'class', 'continue', 'do', 'dynamicparam',
            'else', 'elseif', 'end', 'exit', 'filter', 'for', 'foreach', 'function',
            'if', 'in', 'param', 'return', 'switch', 'throw', 'trap', 'try', 'until', 'using', 'while', 'static',
            '_', 'args', 'error', 'home', 'host', 'input', 'lastexitcode', 'matches', 'myinvocation',
            'nestedpromptlevel', 'null', 'profile', 'psboundparameters', 'pscmdlet', 'pscommandpath',
            'psculture', 'psdebugcontext', 'pshome', 'psitem', 'psscriptroot', 'psuiculture', 'psversiontable',
            'pwd', 'shellid', 'stacktrace', 'this', 'true', 'false',
            'string', 'char', 'bool', 'byte', 'sbyte', 'short', 'ushort', 'int', 'uint', 'long', 'ulong',
            'float', 'double', 'decimal', 'datetime', 'timespan', 'guid', 'version', 'uri', 'nullable',
            'system.object', 'system.string', 'system.char', 'system.boolean', 'system.byte', 'system.sbyte',
            'system.int16', 'system.uint16', 'system.int32', 'system.uint32', 'system.int64', 'system.uint64',
            'system.single', 'system.double', 'system.decimal', 'system.datetime', 'system.timespan',
            'system.guid', 'system.version', 'system.uri', 'system.array'
        }
        
        self.common_cmdlets = {
            'Get-ChildItem', 'Set-Location', 'Get-Content', 'Add-Content', 'Set-Content', 'Copy-Item',
            'Remove-Item', 'Move-Item', 'Test-Path', 'Invoke-WebRequest', 'Invoke-RestMethod', 'Invoke-Expression',
            'ConvertTo-Json', 'ConvertFrom-Json', 'Export-Csv', 'Import-Csv', 'Select-Object', 'Where-Object',
            'ForEach-Object', 'New-Object', 'Get-Process', 'Start-Process', 'Stop-Process', 'Get-Service',
            'Start-Service', 'Stop-Service', 'Get-WmiObject', 'Invoke-Command', 'New-PSDrive', 'Get-Item',
            'Get-ItemProperty', 'Set-ItemProperty', 'Get-ExecutionPolicy', 'Set-ExecutionPolicy'
        }

    def _get_function_context(self, variable: str, content: str) -> Optional[str]:
        """
        Determine if a variable is defined inside a function.
        
        Args:
            variable: The variable name (with $ prefix)
            content: The PowerShell script content
            
        Returns:
            Function name if variable is found in a function context, None otherwise
        """
        var_name = variable[1:]  # Remove $ prefix
        
        # Iterate through all renamed functions
        for func_name in self.function_mapping.keys():
            # Pattern to find function definition and its body
            func_pattern = rf'(?is)function\s+{re.escape(func_name)}\s*{{(.*?)}}'
            
            for match in re.finditer(func_pattern, content):
                func_body = match.group(1)
                
                # Check if variable is assigned in function body
                if re.search(rf'\${re.escape(var_name)}\s*=', func_body):
                    return func_name
                
                # Check if variable is in param block
                param_match = re.search(r'(?is)param\s*\((.*?)\)', func_body)
                if param_match and re.search(rf'\${re.escape(var_name)}\b', param_match.group(1)):
                    return func_name
        
        return None

    def transform(self, content: str) -> str:
        self.variable_mapping = {}
        self.function_mapping = {}
        self.map_tracker = {"Functions": {}, "Variables": {}}
        
        self._identify_variables(content)
        self._identify_functions(content)
        logger.info(f"Renaming {len(self.variable_mapping)} variables and {len(self.function_mapping)} functions")
        
        transformed = content
        
        # Replace function names first
        for original, new_name in self.function_mapping.items():
            pattern = rf'(?i)(function\s+){re.escape(original)}\b|\b{re.escape(original)}\b'
            transformed = re.sub(pattern, lambda m: f"{m.group(1)}{new_name}" if m.group(1) else new_name, transformed)
            self.map_tracker["Functions"][original] = {
                "new_name": new_name,
                "Variables": {}  # Will be populated later
            }
        
        # Replace variables and populate tracker
        for original, new_name in self.variable_mapping.items():
            var_name = original[1:]  # Remove $
            pattern = rf'(?i)(\$){re.escape(var_name)}\b(?!\()'  # Exclude method calls
            
            # Track variable scope
            function_context = self._get_function_context(original, content)
            if function_context:
                self.map_tracker["Functions"][function_context]["Variables"][original] = new_name
            else:
                self.map_tracker["Variables"][original] = new_name  # Track global variables
            
            transformed = re.sub(pattern, rf'\1{new_name[1:]}', transformed)
        
        # Replace ${function:...} references
        transformed = re.sub(
            r'(\$\{function:\s*)([^}]+)(\s*\})',
            lambda m: f"{m.group(1)}{self.function_mapping.get(m.group(2).strip(), m.group(2))}{m.group(3)}",
            transformed,
            flags=re.IGNORECASE
        )
        
        # Replace variables (case-insensitive)
        for original, new_name in self.variable_mapping.items():
            var_name = original[1:]  # Remove $
            pattern = rf'(?i)(\$){re.escape(var_name)}\b(?!\()'  # Exclude method calls like $var.Method()
            transformed = re.sub(pattern, rf'\1{new_name[1:]}', transformed)
            
        # Replace dictionary keys (e.g., ["Stream"] -> ["RenamedVar"])
        def replace_dict_key(match: re.Match) -> str:
            quote = match.group(1)
            key = match.group(2)
            new_var = self.variable_mapping.get(f"${key}", None)
            return f'[{quote}{new_var[1:]}{quote}]' if new_var else match.group(0)
        
        transformed = re.sub(
            r'\[(["\'])([a-zA-Z0-9_]+)\1\]',
            replace_dict_key,
            transformed,
            flags=re.IGNORECASE
        )
        
        # Replace variables/functions inside quoted strings
        def replace_in_quotes(match: re.Match) -> str:
            quote = match.group(1)
            text = match.group(2)
            replacements = {**self.function_mapping, **{k[1:]: v[1:] for k, v in self.variable_mapping.items()}}
            for orig, new in replacements.items():
                text = re.sub(rf'(?i)\b{re.escape(orig)}\b', new, text)
            return f"{quote}{text}{quote}"
        
        transformed = re.sub(r'(["\'])(.*?)\1', replace_in_quotes, transformed, flags=re.DOTALL)
        
        # Preserve special namespaces (e.g., ${env:...})
        transformed = re.sub(
            r'\$\{(env|variable|function):[^}]+\}',
            lambda m: m.group(0),
            transformed,
            flags=re.IGNORECASE
        )
        
        return transformed
    
    def get_stats(self) -> Dict[str, int]:
        """Get accurate statistics including global and function-local variables."""
        total_variables = len(self.variable_mapping)
        total_functions = len(self.function_mapping)
        return {
            "renamed_identifiers": total_variables + total_functions,
            "variables_renamed": total_variables,
            "functions_renamed": total_functions
        }
    
    def _identify_variables(self, content: str) -> None:
        var_patterns = [
            r'(?i)\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=[^=]',  # $var = assignments
            r'(?i)\[[^\]]*?\]\s*\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=',  # [type]$var = 
            r'(?i)foreach\s*\(\s*\$([a-zA-Z_][a-zA-Z0-9_]*)\s+in',  # foreach ($var in ...)
            r'\[\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']\s*\]'  # ["var"] keys
        ]
        
        for pattern in var_patterns:
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                if var_name:
                    full_var = f"${var_name}"
                    if (
                        full_var.lower() not in (kw.lower() for kw in self.reserved_keywords)
                        and full_var not in self.variable_mapping
                    ):
                        new_name = f"${random_name(8)}"
                        while new_name in self.variable_mapping.values():
                            new_name = f"${random_name(8)}"
                        self.variable_mapping[full_var] = new_name
        
        # Handle param blocks
        param_block_pattern = r'(?i)param\s*\((.*?)\)'
        for match in re.finditer(param_block_pattern, content, flags=re.DOTALL):
            param_contents = match.group(1)
            for var in re.findall(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', param_contents):
                full_var = f"${var}"
                if (
                    full_var.lower() not in (kw.lower() for kw in self.reserved_keywords)
                    and full_var not in self.variable_mapping
                ):
                    new_name = f"${random_name(8)}"
                    while new_name in self.variable_mapping.values():
                        new_name = f"${random_name(8)}"
                    self.variable_mapping[full_var] = new_name
    
    def _identify_functions(self, content: str) -> None:
        func_pattern = r'(?i)^\s*function\s+([a-zA-Z0-9_-]+)\b'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            if func_name and func_name.lower() not in (kw.lower() for kw in self.reserved_keywords):
                if func_name not in self.function_mapping and func_name not in self.common_cmdlets:
                    new_name = random_name(10)
                    while new_name in self.function_mapping.values():
                        new_name = random_name(10)
                    self.function_mapping[func_name] = new_name