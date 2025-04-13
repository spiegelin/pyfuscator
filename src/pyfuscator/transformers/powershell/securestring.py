"""
PowerShell SecureString obfuscation transformer.
"""
import re
import random
import base64
from typing import Match, Dict

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class SecureStringTransformer:
    """Transformer that obfuscates strings in PowerShell scripts using SecureString."""
    
    def __init__(self, use_key: bool = True):
        """
        Initialize the transformer.
        
        Args:
            use_key: Whether to use encryption key for more security
        """
        self.use_key = use_key
        self.count = 0  # Track number of strings obfuscated
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by obfuscating strings with SecureString.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with SecureString-obfuscated strings
        """
        self.count = 0
        
        # Find string literals (both single and double quotes)
        # This pattern handles basic cases and prioritizes longer strings
        pattern = r'(?<![\+\'"])("(?:[^"\\]|\\.){10,}"|\'(?:[^\'\\]|\\.){10,}\')(?![\+])'
        
        def replace_string(match: Match) -> str:
            """Replace string with SecureString obfuscated version."""
            original = match.group(1)
            if "SecureString" in original:  # Skip already obfuscated strings
                return original
                
            # Skip strings that are already obfuscated
            if '+' in original or '$' in original:
                return original
                
            self.count += 1
            return self._obfuscate_with_securestring(original)
        
        transformed = re.sub(pattern, replace_string, content)
        
        logger.info(f"Obfuscated {self.count} strings with SecureString in PowerShell script")
        return transformed
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about SecureString obfuscation.
        
        Returns:
            Dict with statistics about SecureString obfuscated strings
        """
        return {
            "secure_strings": self.count
        }
    
    def _obfuscate_with_securestring(self, string_literal: str) -> str:
        """
        Obfuscate a string literal using SecureString.
        
        Args:
            string_literal: The string literal to obfuscate
            
        Returns:
            Obfuscated string using SecureString
        """
        # Extract the actual string content
        quote_char = string_literal[0]
        string_content = string_literal[1:-1]
        
        # Generate random variable names
        secure_var = f"${random_name(6)}"
        plain_var = f"${random_name(6)}"
        
        if self.use_key:
            # More secure approach using a random encryption key
            key_var = f"${random_name(6)}"
            
            # Create a random 16-byte AES key
            key_bytes = bytes([random.randint(1, 255) for _ in range(16)])
            key_base64 = base64.b64encode(key_bytes).decode('ascii')
            
            # Create the obfuscated code
            return f"""
$data = '{string_content}'
{key_var} = [byte[]]@({','.join([str(b) for b in key_bytes])})
{secure_var} = ConvertTo-SecureString -String $data -AsPlainText -Force | ConvertFrom-SecureString -Key {key_var}
{plain_var} = ConvertTo-SecureString -String {secure_var} -Key {key_var} | ForEach-Object {{
    [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($_))
}}
{plain_var}
"""
        # Simpler approach using DPAPI (machine/user specific)
        return f"""
{secure_var} = ConvertTo-SecureString '{string_content}' -AsPlainText -Force | ConvertFrom-SecureString
{plain_var} = ConvertTo-SecureString -String {secure_var} | ForEach-Object {{
    [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($_))
}}
{plain_var}
""" 