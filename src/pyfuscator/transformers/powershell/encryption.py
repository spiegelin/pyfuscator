"""
PowerShell encryption transformer.

This transformer encrypts PowerShell scripts using PowerShell's SecureString capabilities,
with a fixed key for later decryption.
"""
import random
import base64
import subprocess
import platform
import tempfile
import os
import string
from typing import Dict, Any, Optional, Tuple

from pyfuscator.core.transformer import Transformer
from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class EncryptScript(Transformer):
    """Transformer that encrypts PowerShell scripts using SecureString with a fixed key."""
    
    def __init__(self, key_size: int = 32):
        """
        Initialize the transformer.
        
        Args:
            key_size: Size of the encryption key (default: 32 bytes for 256-bit key)
        """
        super().__init__()
        self.key_size = key_size
        self.ps_cmd = "powershell" if platform.system() == "Windows" else "pwsh"
        self.stats = {
            'original_size': 0,
            'encrypted_size': 0,
            'encryption_completed': False
        }
    
    def transform(self, content: str) -> str:
        """
        Transform PowerShell script by encrypting it.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Self-decrypting PowerShell script
        """
        if not content.strip():
            logger.warning("Empty content provided to EncryptScript transformer")
            return content
        
        self.stats['original_size'] = len(content)
        
        try:
            # Encrypt the script content
            encrypted_payload = self._encrypt_content(content)
            
            # Generate the loader script
            loader_script = self._generate_loader_script(encrypted_payload)
            
            self.stats['encrypted_size'] = len(loader_script)
            self.stats['encryption_completed'] = True
            
            logger.info(f"PowerShell script encrypted successfully. Original size: {self.stats['original_size']} bytes, Encrypted size: {self.stats['encrypted_size']} bytes")
            return loader_script
        except Exception as e:
            logger.error(f"Failed to encrypt PowerShell script: {str(e)}")
            # Return original content if encryption fails
            return content
    
    def _encrypt_content(self, content: str) -> str:
        """
        Encrypt the content using PowerShell's SecureString.
        
        Args:
            content: The content to encrypt
            
        Returns:
            Encrypted content as a string
        """
        # Write content to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ps1')
        temp_path = temp_file.name
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # PowerShell script to encrypt the content
            ps_script = f"""
                try {{
                    $key = (1..{self.key_size})
                    $keyBytes = [byte[]]$key
                    $originalCode = Get-Content -Path "{temp_path.replace('\\', '\\\\')}" -Raw
                    $secure = ConvertTo-SecureString $originalCode -AsPlainText -Force
                    $encrypted = ConvertFrom-SecureString -SecureString $secure -Key $keyBytes
                    Write-Output $encrypted
                }} catch {{
                    Write-Error "Error: $($_.Exception.Message)"
                    exit 1
                }}
            """
            
            # Create a temporary file for the encryption script
            encrypt_script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ps1')
            encrypt_script_path = encrypt_script_file.name
            
            with open(encrypt_script_path, 'w', encoding='utf-8') as f:
                f.write(ps_script)
            
            # Run the PowerShell encryption script
            result = subprocess.run([self.ps_cmd, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", encrypt_script_path], 
                                  capture_output=True, text=True, check=True)
            
            encrypted_output = result.stdout.strip()
            if not encrypted_output:
                raise ValueError("No encryption output was received")
            
            return encrypted_output
        except subprocess.CalledProcessError as e:
            logger.error(f"PowerShell encryption error: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise
        finally:
            # Clean up temp files
            try:
                os.unlink(temp_path)
                os.unlink(encrypt_script_path)
            except:
                pass
    
    def _generate_loader_script(self, encrypted_payload: str) -> str:
        """
        Generate a self-decrypting PowerShell script.
        
        Args:
            encrypted_payload: The encrypted script content
            
        Returns:
            A PowerShell script that decrypts and executes the payload
        """
        # Add random whitespace and variable names for obfuscation
        var_key = f"$k{random_name(3)}"
        var_encrypted = f"$e{random_name(4)}"
        var_secure = f"$s{random_name(3)}"
        var_plain = f"$p{random_name(4)}"
        
        # Format the encrypted payload with line breaks for better readability
        formatted_payload = self._format_multiline_string(encrypted_payload)
        
        # Generate the loader script
        loader = f"""
# Self-decrypting PowerShell script loader
# The key must be the same as the one used during encryption
{var_key} = [byte[]](1..{self.key_size})

# Encrypted payload (generated using ConvertFrom-SecureString)
{var_encrypted} = @"
{formatted_payload}
"@

try {{
    # Convert the encrypted string back into a SecureString
    {var_secure} = ConvertTo-SecureString -String {var_encrypted} -Key {var_key}
    
    # Extract the plain-text string
    {var_plain} = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR({var_secure})
    )
    
    # Execute the decrypted script
    Invoke-Expression {var_plain}
}} catch {{
    Write-Error "Decryption or execution error: $($_.Exception.Message)"
    exit 1
}}
"""
        return loader
    
    def _format_multiline_string(self, content: str, width: int = 80) -> str:
        """
        Format a long string into multiple lines for better readability.
        
        Args:
            content: The string to format
            width: Maximum line width
            
        Returns:
            Formatted multiline string
        """
        lines = []
        for i in range(0, len(content), width):
            lines.append(content[i:i+width])
        return '\n'.join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the transformation.
        
        Returns:
            Dictionary with transformation statistics
        """
        return self.stats 

class PowerShellEncryptor(Transformer):
    """Transformer that encrypts PowerShell scripts using ConvertTo-SecureString."""
    
    def __init__(self, encrypt_full: bool = True):
        """
        Initialize the PowerShell encryption transformer.
        
        Args:
            encrypt_full: Whether to encrypt the entire script (True) or parts of it (False)
        """
        super().__init__()
        self.encrypt_full = encrypt_full
        self.stats = {
            "encrypted": False
        }
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by encrypting it.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            The encrypted PowerShell script
        """
        if not content.strip():
            return content
            
        if self.encrypt_full:
            # Encrypt the entire script
            encrypted_script = self._encrypt_full_script(content)
            self.stats["encrypted"] = True
            logger.info("Encrypted the entire PowerShell script")
            return encrypted_script
        else:
            # In future versions, implement partial encryption
            logger.warning("Partial encryption not yet implemented, using full encryption")
            encrypted_script = self._encrypt_full_script(content)
            self.stats["encrypted"] = True
            logger.info("Encrypted the entire PowerShell script")
            return encrypted_script
    
    def _encrypt_full_script(self, content: str) -> str:
        """
        Encrypt the entire PowerShell script.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            The encrypted PowerShell launcher script
        """
        # Generate a random encryption key
        key = self._generate_random_key(32)
        
        # Base64 encode the script content
        base64_content = base64.b64encode(content.encode('utf-16le')).decode('ascii')
        
        # Create the encrypted launcher script
        encrypted_script = self._create_secure_string_launcher(base64_content, key)
        
        return encrypted_script
    
    def _generate_random_key(self, length: int = 32) -> str:
        """
        Generate a random encryption key.
        
        Args:
            length: The length of the key
            
        Returns:
            A random key string
        """
        char_set = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?/"
        return ''.join(random.choice(char_set) for _ in range(length))
    
    def _create_secure_string_launcher(self, base64_content: str, key: str) -> str:
        """
        Create a PowerShell launcher script that decrypts and executes the encrypted content.
        
        Args:
            base64_content: The Base64-encoded script content
            key: The encryption key
            
        Returns:
            A PowerShell launcher script
        """
        # Create variable names using random strings for obfuscation
        encrypted_var = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        key_var = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        secure_var = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        
        # Create the launcher script
        launcher = f"""
# PowerShell Encrypted Script
$({key_var}) = '{key}'
$({encrypted_var}) = @'
{base64_content}
'@

# Convert to secure string and decrypt
$({secure_var}) = ConvertTo-SecureString -String $({encrypted_var}) -Key ([System.Text.Encoding]::ASCII.GetBytes($({key_var})))
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($({secure_var}))
$DecryptedScript = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

# Execute the decrypted script
Invoke-Expression $DecryptedScript
"""
        return launcher 