"""
PowerShell command and function tokenization transformer.
"""
import re
import random
import string
from typing import List, Dict, Set, Any, Tuple

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger

class CommandTokenizer(Transformer):
    """Transformer that tokenizes PowerShell commands and functions for obfuscation."""
    
    def __init__(self, min_token_size: int = 1, max_token_size: int = 3, tokenize_functions: bool = True):
        """
        Initialize the transformer.
        
        Args:
            min_token_size: Minimum size of tokens
            max_token_size: Maximum size of tokens
            tokenize_functions: Whether to tokenize function names as well
        """
        super().__init__()
        self.min_token_size = min_token_size
        self.max_token_size = max_token_size
        self.tokenize_functions = tokenize_functions
        self.stats = {
            "tokenized_commands": 0,
            "tokenized_functions": 0,
            "total_tokenized": 0
        }
        
        # Comprehensive list of common PowerShell cmdlets that we want to tokenize
        self.target_cmdlets = [
            # Common execution cmdlets
            'Invoke-Expression', 'Invoke-WebRequest', 'Invoke-RestMethod', 
            'Invoke-Command', 'iex', 'irm', 'icm',
            
            # Process and service management
            'Start-Process', 'Stop-Process', 'Get-Process', 'Wait-Process',
            'Get-Service', 'Start-Service', 'Stop-Service', 'Restart-Service',
            
            # Object manipulation
            'New-Object', 'Get-Member', 'Select-Object', 'ForEach-Object',
            'Where-Object', 'Sort-Object', 'Group-Object', 'Measure-Object',
            
            # File system operations
            'Get-Content', 'Set-Content', 'Out-File', 'Add-Content',
            'Get-ChildItem', 'Get-Item', 'Remove-Item', 'Copy-Item',
            'Move-Item', 'Test-Path', 'New-Item', 'Set-Location',
            'Get-Location', 'Push-Location', 'Pop-Location',
            
            # Module management
            'Import-Module', 'Get-Module', 'Remove-Module', 'Export-ModuleMember',
            
            # Output and formatting
            'Write-Host', 'Write-Output', 'Write-Error', 'Write-Warning',
            'Write-Verbose', 'Format-List', 'Format-Table', 'Out-String',
            'Out-GridView', 'Out-Default', 'Out-Null',
            
            # Variable management
            'Set-Variable', 'Get-Variable', 'Clear-Variable', 'Remove-Variable',
            
            # Alias management
            'Get-Alias', 'Set-Alias', 'New-Alias', 'Remove-Alias',
            
            # Event management
            'Register-ObjectEvent', 'Unregister-Event', 'Get-Event', 'Wait-Event',
            
            # Networking
            'Test-Connection', 'Test-NetConnection', 'Get-NetAdapter', 
            'Get-NetIPAddress', 'Get-DnsClientServerAddress',
            
            # Security
            'ConvertTo-SecureString', 'ConvertFrom-SecureString', 'Get-Credential',
            'Get-ExecutionPolicy', 'Set-ExecutionPolicy', 'Unprotect-CmsMessage',
            
            # Scheduling
            'Register-ScheduledJob', 'Get-ScheduledJob', 'Start-Job', 'Get-Job',
            'Receive-Job', 'Stop-Job', 'Remove-Job',
            
            # Common aliases and additional commands
            'cd', 'ls', 'dir', 'echo', 'type', 'cat', 'copy', 'cp', 'move', 'mv',
            'rm', 'del', 'rd', 'rmdir', 'mkdir', 'md', 'pwd', 'gci', 'gc', 'sc',
            'iwr', 'curl', 'wget', 'select', 'sort', 'group', 'gps', 'gsv'
        ]
        
        # Regex patterns for identifying PowerShell commands and functions
        self.command_pattern = r'\b(Get-|Set-|New-|Remove-|Add-|Clear-|Invoke-|Import-|Export-|Start-|Stop-|Restart-|Out-|Test-|Measure-|ConvertTo-|ConvertFrom-|Format-|Select-|Sort-|Group-|Where-|ForEach-|Update-|Write-|Move-|Copy-|Split-|Join-|Compare-|Find-|Enable-|Disable-|Wait-|Show-|Watch-|Use-|Push-|Pop-|Read-)[a-zA-Z]+\b'
        self.function_pattern = r'function\s+([a-zA-Z0-9_-]+)\s*\{'
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by tokenizing commands and functions.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with tokenized commands and functions
        """
        self.stats["tokenized_commands"] = 0
        self.stats["tokenized_functions"] = 0
        
        if not content.strip():
            return content
        
        transformed = content
        
        # First, find all user-defined functions in the script
        user_functions = self._find_user_functions(transformed)
        
        # First, tokenize functions to avoid conflicts
        if self.tokenize_functions:
            transformed, function_count = self._tokenize_functions(transformed, user_functions)
            self.stats["tokenized_functions"] = function_count
        
        # Use a regex pattern that matches cmdlets with parameters that might follow
        # We'll tokenize the command in a way that handles arguments correctly
        for cmdlet in self.target_cmdlets:
            # Pattern to match complete cmdlet invocations including arguments
            # Use lookahead to ensure we match just the command and not arguments
            pattern = r'(?<!["\'\w-])(' + re.escape(cmdlet) + r')(?=\s|\(|\Z)'
            
            # Find all matches before replacing to avoid modifying the same content multiple times
            matches = list(re.finditer(pattern, transformed))
            
            # Process matches in reverse order to maintain correct positions
            for match in reversed(matches):
                cmd = match.group(1)
                start, end = match.span(1)
                
                # Choose a tokenization technique that can handle command invocation properly
                technique = random.choice([
                    self._simple_tokenize,
                    self._char_join_technique,
                    self._variable_based_tokenization
                ])
                
                # Generate the tokenized command with invocation support
                tokenized_cmd = technique(cmd)
                
                # Replace just the command name, not its arguments
                transformed = transformed[:start] + tokenized_cmd + transformed[end:]
                self.stats["tokenized_commands"] += 1
        
        self.stats["total_tokenized"] = self.stats["tokenized_commands"] + self.stats["tokenized_functions"]
        logger.info(f"Tokenized {self.stats['tokenized_commands']} commands and {self.stats['tokenized_functions']} functions in PowerShell script")
        return transformed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tokenization."""
        return self.stats
    
    def _find_user_functions(self, content: str) -> Set[str]:
        """
        Extract user-defined function names from the PowerShell script.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Set of function names defined in the script
        """
        # Pattern to match function definitions: function Name {...} or filter Name {...}
        function_pattern = re.compile(r'\b(?:function|filter)\s+([A-Za-z0-9_-]+)', re.IGNORECASE)
        
        # Find all function names
        return set(function_pattern.findall(content))
    
    def _tokenize_functions(self, content: str, user_functions: Set[str]) -> Tuple[str, int]:
        """
        Tokenize PowerShell functions in the script.
        
        Args:
            content: The PowerShell script content
            user_functions: Set of user-defined function names
            
        Returns:
            Tuple of (transformed content, count of tokenized functions)
        """
        function_count = 0
        transformed = content
        
        for func_name in user_functions:
            # Skip very short function names (like 'f' or 'a') and common PowerShell terms
            if len(func_name) <= 1 or func_name.lower() in ['if', 'for', 'while', 'switch']:
                continue
                
            # Match function name outside of the function definition, string literals, and comments
            # Use a simpler pattern that doesn't require variable-width lookbehind
            pattern = r'\b(' + re.escape(func_name) + r')\b(?!["\'])'
            
            # Find all matches before replacing
            matches = list(re.finditer(pattern, transformed))
            
            # Process matches in reverse order, but filter out function definitions
            filtered_matches = []
            for match in matches:
                # Check if this match is part of a function definition
                pos = match.start()
                prefix = transformed[max(0, pos-30):pos].strip()
                if not (prefix.endswith('function ') or prefix.endswith('filter ')):
                    filtered_matches.append(match)
            
            # Process matches in reverse order
            for match in sorted(filtered_matches, key=lambda m: m.start(), reverse=True):
                func = match.group(1)
                
                # Choose a tokenization technique
                technique = random.choice([
                    self._simple_tokenize,
                    self._char_join_technique,
                    self._variable_based_tokenization
                ])
                
                tokenized_func = technique(func)
                start, end = match.span(1)
                
                # Replace the function name with its tokenized version
                transformed = transformed[:start] + tokenized_func + transformed[end:]
                function_count += 1
        
        return transformed, function_count
    
    def _generate_tokenized_name(self) -> str:
        """
        Generate a random tokenized function name.
        
        Returns:
            A randomly generated function name
        """
        prefixes = ['tmp', 'fn', 'proc', 'exec', 'run']
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return f"{prefix}_{suffix}"
    
    def _simple_tokenize(self, command: str) -> str:
        """
        Simple tokenization by splitting a command into smaller pieces and concatenating.
        
        Args:
            command: The command to tokenize
            
        Returns:
            Tokenized command string with command invocation support
        """
        # Random token size concatenation
        tokens = []
        i = 0
        command_len = len(command)
        
        while i < command_len:
            token_size = random.randint(self.min_token_size, min(self.max_token_size, command_len - i))
            tokens.append(f"'{command[i:i+token_size]}'")
            i += token_size
        
        # Add & to make this a command invocation with correct syntax    
        return f"&({'+'.join(tokens)})"
    
    def _char_join_technique(self, command: str) -> str:
        """
        Tokenize a command using character array join technique.
        
        Args:
            command: The command to tokenize
            
        Returns:
            The tokenized command string with command invocation support
        """
        chars = [f"'{c}'" for c in command]
        chars_str = ','.join(chars)
        # Add & to make this a command invocation with correct syntax
        return f"&([char[]]({chars_str})-join'')"
    
    def _environment_variable_technique(self, command: str) -> str:
        """
        Tokenize a command using environment variable technique.
        
        Args:
            command: The command to tokenize
            
        Returns:
            The tokenized command string
        """
        # Split the command into segments
        segments = []
        current_segment = ""
        
        for char in command:
            current_segment += char
            if random.random() < 0.3 and current_segment:  # 30% chance to split
                segments.append(current_segment)
                current_segment = ""
        
        if current_segment:
            segments.append(current_segment)
        
        # Create environment variables for each segment
        env_vars = []
        for i, segment in enumerate(segments):
            var_name = f"{''.join(random.choice(string.ascii_uppercase) for _ in range(4))}"
            env_vars.append(f"$env:{var_name}='{segment}'")
        
        var_names = [f"$env:{var.split('=')[0].replace('$env:', '')}" for var in env_vars]
        var_concat = '+'.join(var_names)
        
        # CRITICAL FIX: Use proper command invocation syntax
        return f"& (& {{ {'; '.join(env_vars)}; ({var_concat}) }})"
    
    def _string_format_technique(self, command: str) -> str:
        """
        Tokenize a command using string format technique.
        
        Args:
            command: The command to tokenize
            
        Returns:
            The tokenized command string
        """
        # Randomly split the command into segments
        split_points = sorted(random.sample(range(1, len(command)), min(len(command) - 1, 3)))
        segments = []
        last_point = 0
        
        for point in split_points:
            segments.append(command[last_point:point])
            last_point = point
        
        segments.append(command[last_point:])
        
        # Create a format string with placeholders
        format_string = '{0}' * len(segments)
        format_args = ','.join([f"'{segment}'" for segment in segments])
        
        # CRITICAL FIX: Add & operator for command invocation
        return f"& ([string]::Format('{format_string}',{format_args}))"
    
    def _variable_based_tokenization(self, command: str) -> str:
        """
        Variable-based concatenation with randomized variable names.
        
        Args:
            command: The command to tokenize
            
        Returns:
            Tokenized command expression with command invocation support
        """
        parts = []
        i = 0
        command_len = len(command)
        
        while i < command_len:
            token_size = random.randint(self.min_token_size, min(self.max_token_size, command_len - i))
            # Generate a random var name suffix for added obfuscation
            var_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
            parts.append((f"$p{i}_{var_suffix}", command[i:i+token_size]))
            i += token_size
        
        # Create variable assignments with a $
        var_assignments = []
        for var_name, value in parts:
            var_assignments.append(f"{var_name}='{value}'")
        
        # Create concatenation expression
        concat_expr = '+'.join([var_name for var_name, _ in parts])
        
        # CRITICAL FIX: Change the format to match the working syntax
        # Return syntax that works with arguments, using & operator outside the script block
        return f"& (& {{ {'; '.join(var_assignments)}; ({concat_expr}) }})" 