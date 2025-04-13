"""
PowerShell Base64 encoding transformer.
"""
import re
import base64
import random
from typing import Dict, Any, List

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger

class Base64Encoder(Transformer):
    """Transformer that encodes portions of a PowerShell script using Base64."""
    
    def __init__(self, encode_blocks: bool = True, encode_full: bool = False, encode_individual: bool = False):
        """
        Initialize the transformer.
        
        Args:
            encode_blocks: Whether to encode individual script blocks (default: True)
            encode_full: Whether to encode the entire script if no blocks are encoded (default: False)
            encode_individual: Whether to encode individual commands instead of blocks (default: False)
        """
        super().__init__()
        self.encode_blocks = encode_blocks
        self.encode_full = encode_full
        self.encode_individual = encode_individual
        self.stats = {
            "blocks_encoded": 0,
            "commands_encoded": 0,
            "encoded_full_script": False
        }
        
        # Pattern to match script blocks and commands
        self.script_block_pattern = re.compile(r'({[^{}]*(?:{[^{}]*}[^{}]*)*})')
        self.command_pattern = re.compile(r'((?:Get|Set|New|Remove|Add|Clear|Invoke|Start|Stop)-\w+(?:\s+-\w+\s+[^;]+)?)')
        
        # Pattern to identify control structures (if, for, foreach, switch, while)
        self.control_structure_pattern = re.compile(r'\b(if|switch|for|foreach|while|do|try|catch|finally)\b\s*(?:\([^)]*\))?\s*{')
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by encoding script blocks or the entire script.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with Base64-encoded portions
        """
        self.stats["blocks_encoded"] = 0
        self.stats["commands_encoded"] = 0
        self.stats["encoded_full_script"] = False
        
        if not content.strip():
            return content
        
        transformed = content
        
        # Option 1: Encode script blocks (but avoid control structures and blocks with variables)
        if self.encode_blocks:
            transformed = self._encode_blocks(transformed)
        
        # Option 2: Encode individual commands
        if self.encode_individual and not self.stats["blocks_encoded"]:
            transformed = self._encode_commands(transformed)
        
        # Option 3: If no blocks or commands were encoded and encode_full is set, encode the entire script
        if self.encode_full and not (self.stats["blocks_encoded"] or self.stats["commands_encoded"]):
            transformed = self._encode_full_script(content)
            self.stats["encoded_full_script"] = True
            logger.info("Encoded entire script using Base64")
        
        return transformed
    
    def _encode_blocks(self, content: str) -> str:
        """
        Encode simple script blocks within the content, avoiding control structures and variables.
        
        Args:
            content: The script content
            
        Returns:
            Content with encoded blocks
        """
        transformed = content
        
        # Find all top-level blocks with a minimum size
        matches = []
        for match in self.script_block_pattern.finditer(transformed):
            block_content = match.group(1)
            block_start, block_end = match.span(0)
            
            # Skip empty blocks or very small blocks
            if len(block_content.strip()) <= 20:
                continue
            
            # Skip if block contains variables
            if self._contains_variables(block_content):
                continue
                
            # Skip if block is part of a control structure or contains one
            if self._is_control_structure(transformed, block_start) or self._contains_control_structure(block_content):
                continue
                
            matches.append(match)
        
        # If we found candidate blocks, randomly select some to encode
        if matches:
            # Select a subset of blocks to encode (30-50%)
            num_to_encode = max(1, int(len(matches) * random.uniform(0.3, 0.5)))
            blocks_to_encode = random.sample(matches, min(num_to_encode, len(matches)))
            
            # Process blocks in reverse order to maintain correct positions
            for match in sorted(blocks_to_encode, key=lambda m: m.start(), reverse=True):
                block_content = match.group(1)
                
                # Encode the block
                encoded_block = self._encode_base64(block_content)
                
                # Replace the block with its encoded version
                start, end = match.span(0)  # Include the curly braces
                transformed = transformed[:start] + encoded_block + transformed[end:]
                self.stats["blocks_encoded"] += 1
        
        if self.stats["blocks_encoded"] > 0:
            logger.info(f"Encoded {self.stats['blocks_encoded']} script blocks using Base64")
        
        return transformed
    
    def _is_control_structure(self, content: str, position: int) -> bool:
        """
        Check if the block at the given position is part of a control structure.
        
        Args:
            content: The script content
            position: The position of the block start
            
        Returns:
            True if it's a control structure, False otherwise
        """
        # Check the preceding characters for control structure keywords with a larger window
        # This helps catch for loop patterns that might be spread across multiple lines
        prefix = content[max(0, position-100):position].strip()
        
        # Specifically check for "for" control structures which might have specific formats
        for_pattern = re.compile(r'\bfor\s*\(.*\$.*\).*{', re.DOTALL)
        if for_pattern.search(prefix):
            return True
        
        return bool(self.control_structure_pattern.search(prefix))
    
    def _contains_control_structure(self, content: str) -> bool:
        """
        Check if the content contains control structures.
        
        Args:
            content: Script content to check
            
        Returns:
            True if control structures found, False otherwise
        """
        return bool(self.control_structure_pattern.search(content))
    
    def _contains_variables(self, content: str) -> bool:
        """
        Check if content contains variable references that would make it unsafe to encode.
        
        Args:
            content: Script content to check
            
        Returns:
            True if variables found, False otherwise
        """
        # Look for variable references ($var)
        var_pattern = r'\$[\w\d_]+|\$\{[\w\d_]+\}|\$\(.*?\)'
        return bool(re.search(var_pattern, content))
    
    def _encode_commands(self, content: str) -> str:
        """
        Encode individual PowerShell commands.
        
        Args:
            content: The script content
            
        Returns:
            Content with encoded commands
        """
        transformed = content
        
        # Find all commands that match our pattern
        matches = list(self.command_pattern.finditer(transformed))
        
        if not matches:
            return transformed
        
        # Select a subset of commands to encode (20-40%)
        num_to_encode = max(1, int(len(matches) * random.uniform(0.2, 0.4)))
        commands_to_encode = random.sample(matches, min(num_to_encode, len(matches)))
        
        # Process commands in reverse order to maintain correct positions
        for match in sorted(commands_to_encode, key=lambda m: m.start(), reverse=True):
            command = match.group(1)
            
            # Only encode commands that are significant (more than 10 chars)
            if len(command) < 10:
                continue
                
            # Encode the command
            encoded_command = f'powershell -EncodedCommand "{self._encode_to_base64(command)}"'
            
            # Replace the command with its encoded version
            start, end = match.span(0)
            transformed = transformed[:start] + encoded_command + transformed[end:]
            self.stats["commands_encoded"] += 1
        
        if self.stats["commands_encoded"] > 0:
            logger.info(f"Encoded {self.stats['commands_encoded']} commands using Base64")
        
        return transformed
    
    def _encode_base64(self, script: str) -> str:
        """
        Encode a script segment using Base64.
        
        Args:
            script: Script content to encode
            
        Returns:
            PowerShell command that decodes and executes the encoded script
        """
        # Encode the script using UTF-16LE (the encoding used by PowerShell)
        encoded = self._encode_to_base64(script)

        # Construct the decoder and executor as a script block that will be immediately invoked.
        # The "&" operator forces the execution of the script block.
        executor = "& { Invoke-Expression ([System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('" + encoded + "'))) }"
        return executor
    
    def _encode_to_base64(self, script: str) -> str:
        """
        Convert a script to Base64 string.
        
        Args:
            script: Script content to encode
            
        Returns:
            Base64 encoded string
        """
        script_bytes = script.encode('utf-16le')
        return base64.b64encode(script_bytes).decode('ascii')
    
    def _encode_full_script(self, script: str) -> str:
        """
        Encode the entire script.
        
        Args:
            script: Full script content to encode
            
        Returns:
            PowerShell launcher script that decodes and executes the original script
        """
        encoded = self._encode_to_base64(script)
        
        # Create a launcher script
        launcher = (
            "$scriptEncoded = '{0}'\n"
            "$scriptBytes = [System.Convert]::FromBase64String($scriptEncoded)\n"
            "$scriptText = [System.Text.Encoding]::Unicode.GetString($scriptBytes)\n"
            "Invoke-Expression $scriptText"
        ).format(encoded)
        
        return launcher 