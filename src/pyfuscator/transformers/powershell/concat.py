"""
PowerShell command tokenization transformer (preserves function names)
"""
import re
import random
from typing import Dict, Set, Any, Tuple, List

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger
from pyfuscator.core.utils import random_name

class CommandTokenizer(Transformer):
    
    def __init__(self, min_token_size: int = 1, max_token_size: int = 3):
        super().__init__()
        self.min_token_size = min_token_size
        self.max_token_size = max_token_size
        self.stats = {"tokenized_commands": 0}

        self.reserved_keywords = {
            'return', 'param', 'begin', 'process', 'end', 'if', 'else',
            'foreach', 'while', 'switch', 'try', 'catch', 'finally', 'throw'
        }

        self.target_cmdlets = [
            'Invoke-Expression', 'Invoke-WebRequest', 'Invoke-RestMethod', 
            'Invoke-Command', 'iex', 'irm', 'icm', 'Start-Process', 'Stop-Process',
            'Get-Process', 'Wait-Process', 'Get-Service', 'Start-Service',
            'Stop-Service', 'Restart-Service', 'New-Object', 'Get-Member',
            'Select-Object', 'ForEach-Object', 'Where-Object', 'Sort-Object',
            'Group-Object', 'Measure-Object', 'Get-Content', 'Set-Content',
            'Out-File', 'Add-Content', 'Get-ChildItem', 'Get-Item', 'Remove-Item',
            'Copy-Item', 'Move-Item', 'Test-Path', 'New-Item', 'Set-Location',
            'Get-Location', 'Push-Location', 'Pop-Location', 'Import-Module',
            'Get-Module', 'Remove-Module', 'Export-ModuleMember', 'Export-Module',
            'Write-Host', 'Write-Output', 'Write-Error', 'Write-Warning',
            'Write-Verbose', 'Format-List', 'Format-Table', 'Out-String',
            'Out-GridView', 'Out-Default', 'Out-Null', 'Format-Wide', 'Out-Host',
            'Out-File', 'Tee-Object', 'Set-Variable', 'Get-Variable',
            'Clear-Variable', 'Remove-Variable', 'Get-Alias', 'Set-Alias',
            'New-Alias', 'Remove-Alias', 'Register-ObjectEvent', 'Unregister-Event',
            'Get-Event', 'Wait-Event', 'Test-Connection', 'Test-NetConnection',
            'Get-NetAdapter', 'Get-NetIPAddress', 'Get-DnsClientServerAddress',
            'ConvertTo-SecureString', 'ConvertFrom-SecureString', 'Get-Credential',
            'Get-ExecutionPolicy', 'Set-ExecutionPolicy', 'Unprotect-CmsMessage',
            'Register-ScheduledJob', 'Get-ScheduledJob', 'Start-Job', 'Get-Job',
            'Receive-Job', 'Stop-Job', 'Remove-Job', 'cd', 'ls', 'dir', 'echo',
            'type', 'cat', 'copy', 'cp', 'move', 'mv', 'rm', 'del', 'rd', 'rmdir',
            'mkdir', 'md', 'pwd', 'gci', 'gc', 'sc', 'iwr', 'curl', 'wget', 'select',
            'sort', 'group', 'gps', 'gsv', 'Get-Random', 'Test-Function',
            'Get-RandomNumber', 'Rename-Item', 'Get-History', 'Get-Command',
            'Get-Help', 'Compare-Object', 'ConvertTo-Html', 'ConvertTo-Csv',
            'Export-Csv', 'Import-Csv', 'New-TimeSpan', 'Clear-Host', '%', '?',
            'ren', 'rni', 'history', 'ghy', 'gcm', 'help', 'man', 'measure',
            'compare', 'diff', 'fl', 'ft', 'fw', 'oh', 'os', 'ogv', 'epcsv',
            'ipcsv', 'new', 'nts', 'saps', 'start', 'sasv', 'spps', 'kill',
            'spsv', 'wait', 'cls', 'clear', 'test', 'gal', 'ipmo', 'epmo', 'gmo',
            'ni', 'ac', 'erase', 'sl', 'gl', 'cpi', 'mi', 'ri', 'ren', 'IEX',
            'New-Object', 'Setup_CMD', 'ConvertTo-HexArray', 'SendPacket', 'Create_SYN'
        ]
        
        self.additional_cmdlets = [
            'Add-Member', 'ConvertFrom-Csv', 'ConvertFrom-Json',
            'ConvertTo-Json', 'ConvertTo-Xml', 'Join-Path', 'Resolve-Path',
            'Split-Path', 'Test-Path', 'New-Guid', 'New-TimeSpan'
        ]
        
        self.target_cmdlets.extend(self.additional_cmdlets)
        self.operators = {
            '-eq', '-ne', '-gt', '-ge', '-lt', '-le', '-like', '-notlike',
            '-match', '-notmatch', '-contains', '-notcontains', '-and', '-or',
            '-xor', '-not', '-replace', '-split', '-join', '-in', '-notin'
        }
        self.operator_map = {}
        self.command_pattern = re.compile(
            r'(?<![\$\.\:\]&\|])\b([A-Za-z_-]+-[A-Za-z_-]+|\b[A-Za-z_-]+)(?=\s|\(|\Z)',
            re.IGNORECASE | re.X
        )
        self.function_pattern = re.compile(
            r'\bfunction\s+([a-zA-Z0-9_-]+)\b',
            re.IGNORECASE
        )
        self.var_subscript_pattern = re.compile(r'\$[\w\.]+\s*\[["\']([^"\']+)["\']\]')
        self.invocation_pattern = re.compile(
            r'(?i)(?:Invoke-Command\s+)?\$[\w\.]+\s*\[["\']([^"\']+)["\']\]',
            re.MULTILINE
        )
        self.protected_pattern = re.compile(
            r'(\.[A-Za-z_]\w*)|'     
            r'\$[^=]+=[^=]|'          
            r'-\w+|'                  
            r'\[[^\]]+\]|'            
            r'\([^\)]*\)|'            
            r'"[^"]*"|'               
            r"'[^']*'",               
            re.IGNORECASE | re.X
        )


        self.command_pattern = re.compile(
            r'(?<!function\s)(?<![\$\.\:\]&\|])\b([A-Za-z_-]+-[A-Za-z_-]+|\b[A-Za-z_-]+)(?=\s|\(|\Z)',
            re.IGNORECASE | re.X
        )
        
        self.function_declaration_pattern = re.compile(
            r'^function\s+([a-zA-Z0-9_-]+)',
            re.MULTILINE | re.IGNORECASE
        )

    def transform(self, content: str) -> str:
        self.stats["tokenized_commands"] = 0
        
        protected_functions = self._find_user_functions(content)
        transformed = self._protect_function_names(content, protected_functions)
        transformed = self._tokenize_commands(transformed, protected_functions)
        
        logger.info(f"Tokenized {self.stats['tokenized_commands']} commands")
        return transformed

    def _find_user_functions(self, content: str) -> Set[str]:
        return {m.group(1) for m in self.function_declaration_pattern.finditer(content)}

    def _protect_function_names(self, content: str, protected: Set[str]) -> str:
        placeholder_map = {}
        for func in protected:
            placeholder = f"__FN_{random_name()}__"
            placeholder_map[placeholder] = func
            content = re.sub(
                rf'\bfunction\s+{re.escape(func)}\b',
                f'function {placeholder}',
                content,
                flags=re.IGNORECASE
            )
        for placeholder, func in placeholder_map.items():
            content = content.replace(placeholder, func)
        return content

    def _tokenize_commands(self, content: str, protected: Set[str]) -> str:
        protected_areas = self._find_protected_areas(content)
        
        for cmdlet in self.target_cmdlets:
            pattern = re.compile(rf'(?<!function\s)(?<![\$\.\:\]&\|])\b({re.escape(cmdlet)})\b(?=\s|\(|\Z)', re.IGNORECASE)
            matches = list(pattern.finditer(content))
            for match in reversed(matches):
                if any(match.start() >= start and match.end() <= end for (start, end) in protected_areas):
                    continue
                if match.group(1) in protected:
                    continue
                
                cmd = match.group(1)
                start, end = match.span(1)
                technique = random.choice([
                    self._simple_tokenize,
                    self._char_join_technique,
                    self._variable_tokenization
                ])
                tokenized_cmd = technique(cmd)
                content = content[:start] + f"& {tokenized_cmd}" + content[end:]
                self.stats["tokenized_commands"] += 1
                
        return content

    def _find_protected_areas(self, content: str) -> List[Tuple[int, int]]:
        protected = []
        for match in self.function_declaration_pattern.finditer(content):
            protected.append((match.start(1), match.end(1)))
        return protected

    def _simple_tokenize(self, command: str) -> str:
        tokens = []
        i = 0
        while i < len(command):
            token_size = random.randint(self.min_token_size, self.max_token_size)
            tokens.append(f"'{command[i:i+token_size]}'")
            i += token_size
        return f"({'+'.join(tokens)})"

    def _char_join_technique(self, command: str) -> str:
        chars = [f"[char]{ord(c)}" for c in command]
        return f"$(-join({','.join(chars)}))"

    def _variable_tokenization(self, command: str) -> str:
        var_name = random_name()
        return f"(${{{var_name}}}='{command}')"

    def get_stats(self) -> Dict[str, Any]:
        return self.stats