"""
PowerShell identifier renaming transformer.
"""
import re
import random
import string
from typing import Dict, List, Set, Tuple, Optional

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class RenameIdentifiers:
    """Transformer that renames variables and functions in PowerShell scripts."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.variable_mapping: Dict[str, str] = {}
        self.function_mapping: Dict[str, str] = {}
        self.reserved_keywords = {
            # PowerShell reserved keywords
            'begin', 'break', 'catch', 'class', 'continue', 'data', 'define', 'do', 'dynamicparam', 'else', 
            'elseif', 'end', 'enum', 'exit', 'filter', 'finally', 'for', 'foreach', 'from', 'function', 
            'hidden', 'if', 'in', 'inlinescript', 'param', 'process', 'return', 'static', 'switch', 
            'throw', 'trap', 'try', 'until', 'using', 'var', 'while', 'workflow', 
            # Common automatic variables
            '$_', '$args', '$error', '$home', '$host', '$input', '$lastexitcode', '$matches', '$myinvocation',
            '$nestedpromptlevel', '$null', '$profile', '$psboundparameters', '$pscmdlet', '$pscommandpath',
            '$psculture', '$psdebugcontext', '$pshome', '$psitem', '$psscriptroot', '$psuiculture', '$psversiontable',
            '$pwd', '$shellid', '$stacktrace', '$this', '$true', '$false'
        }
        self.common_modules = {
            'Microsoft.PowerShell.Utility', 'Microsoft.PowerShell.Management', 'Microsoft.PowerShell.Security',
            'Microsoft.PowerShell.Host', 'Microsoft.WSMan.Management', 'Microsoft.PowerShell.Diagnostics'
        }
        self.common_cmdlets = {
            'Get-ChildItem', 'Set-Location', 'Get-Content', 'Add-Content', 'Set-Content', 'Copy-Item',
            'Remove-Item', 'Move-Item', 'Test-Path', 'Invoke-WebRequest', 'Invoke-RestMethod', 'Invoke-Expression',
            'ConvertTo-Json', 'ConvertFrom-Json', 'Export-Csv', 'Import-Csv', 'Select-Object', 'Where-Object',
            'ForEach-Object', 'New-Object', 'Get-Process', 'Start-Process', 'Stop-Process', 'Get-Service',
            'Start-Service', 'Stop-Service', 'Get-WmiObject', 'Invoke-Command', 'New-PSDrive', 'Get-Item',
            'Get-ItemProperty', 'Set-ItemProperty', 'Get-ExecutionPolicy', 'Set-ExecutionPolicy'
        }
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by renaming identifiers.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with renamed identifiers
        """
        # Reset mappings
        self.variable_mapping = {}
        self.function_mapping = {}
        
        # First pass: identify variables and functions
        self._identify_variables(content)
        self._identify_functions(content)
        
        logger.info(f"Identified {len(self.variable_mapping)} variables and {len(self.function_mapping)} functions to rename")
        
        # Second pass: replace all occurrences
        transformed = content
        
        # Replace function names (must be done before variables to avoid partial matches)
        for original, new_name in self.function_mapping.items():
            # Match only function declarations and function calls (not variable assignments)
            pattern = r'(?i)(function\s+)' + re.escape(original) + r'\b|\b' + re.escape(original) + r'(?=\s*\()'
            transformed = re.sub(pattern, lambda m: m.group(1) + new_name if m.group(1) else new_name, transformed)
        
        # Replace variables
        for original, new_name in self.variable_mapping.items():
            # Match variable with $ prefix, ensuring it's a whole variable name
            pattern = r'(\$)' + re.escape(original[1:]) + r'\b'
            transformed = re.sub(pattern, r'\1' + new_name[1:], transformed)
        
        return transformed
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about renamed identifiers.
        
        Returns:
            Dict with statistics about renamed identifiers
        """
        total_renames = len(self.variable_mapping) + len(self.function_mapping)
        return {
            "renamed_identifiers": total_renames
        }
    
    def _identify_variables(self, content: str) -> None:
        """
        Identify PowerShell variables in the script.
        
        Args:
            content: The PowerShell script content
        """
        # Find variable declarations and assignments
        # Pattern matches $varName = value and [type]$varName = value
        var_pattern = r'\$([a-zA-Z0-9_]+)\s*=|\[.*?\]\$([a-zA-Z0-9_]+)\s*='
        
        for match in re.finditer(var_pattern, content):
            var_name = match.group(1) or match.group(2)
            if var_name:
                full_var_name = f"${var_name}"
                if full_var_name.lower() not in self.reserved_keywords and full_var_name not in self.variable_mapping:
                    # Generate a new random variable name
                    new_name = f"${random_name(5)}"
                    while new_name in self.variable_mapping.values():
                        new_name = f"${random_name(5)}"
                    
                    self.variable_mapping[full_var_name] = new_name
        
        # Find foreach variable declarations
        foreach_pattern = r'(?i)foreach\s*\(\s*\$([a-zA-Z0-9_]+)\s+in'
        
        for match in re.finditer(foreach_pattern, content):
            var_name = match.group(1)
            if var_name:
                full_var_name = f"${var_name}"
                if full_var_name.lower() not in self.reserved_keywords and full_var_name not in self.variable_mapping:
                    # Generate a new random variable name
                    new_name = f"${random_name(5)}"
                    while new_name in self.variable_mapping.values():
                        new_name = f"${random_name(5)}"
                    
                    self.variable_mapping[full_var_name] = new_name
        
        # Find param block variables
        param_pattern = r'(?i)param\s*\(\s*(?:\[.*?\])?\s*\$([a-zA-Z0-9_]+)'
        
        for match in re.finditer(param_pattern, content):
            var_name = match.group(1)
            if var_name:
                full_var_name = f"${var_name}"
                if full_var_name.lower() not in self.reserved_keywords and full_var_name not in self.variable_mapping:
                    # Generate a new random variable name
                    new_name = f"${random_name(5)}"
                    while new_name in self.variable_mapping.values():
                        new_name = f"${random_name(5)}"
                    
                    self.variable_mapping[full_var_name] = new_name
    
    def _identify_functions(self, content: str) -> None:
        """
        Identify PowerShell functions in the script.
        
        Args:
            content: The PowerShell script content
        """
        # Find function declarations
        func_pattern = r'(?i)function\s+([a-zA-Z0-9_-]+)'
        
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            if func_name and func_name.lower() not in self.reserved_keywords and func_name not in self.common_cmdlets:
                if func_name not in self.function_mapping:
                    # Generate a new random function name
                    new_name = random_name(8)
                    while new_name in self.function_mapping.values():
                        new_name = random_name(8)
                    
                    self.function_mapping[func_name] = new_name 