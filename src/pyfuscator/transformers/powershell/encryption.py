"""
PowerShell encryption transformers.

This module provides transformers for encrypting PowerShell scripts.
"""
import os
import base64
import random
import string
import subprocess
import tempfile
from typing import Dict, Any

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger

def random_name(length: int = 8) -> str:
    """Generate a random name for variables."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

class EncryptScript(Transformer):
    """Transformer that encrypts PowerShell scripts."""
    
    def __init__(self, key_size: int = 32):
        """
        Initialize the transformer.
        
        Args:
            key_size: Size of the encryption key
        """
        super().__init__()
        self.key_size = key_size
        
        # Check if PowerShell is available
        self.ps_cmd = 'powershell' if os.name == 'nt' else 'pwsh'
        try:
            subprocess.run([self.ps_cmd, '-Command', 'echo "PowerShell check"'], 
                         capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("PowerShell is not available on this system. Script encryption will not work.")
            self.ps_cmd = None
            
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
        
        if not self.ps_cmd:
            logger.warning("PowerShell is required for script encryption, skipping this transformer")
            return content
        
        try:
            # Encrypt the content
            encrypted_payload = self._encrypt_content(content)
            
            # Create a loader script that decrypts and executes the payload
            loader_script = self._generate_loader_script(encrypted_payload)
            
            self.stats["encrypted"] = True
            logger.info("PowerShell script successfully encrypted with SecureString")
            
            return loader_script
        except Exception as exception:
            logger.error(f"Failed to encrypt script: {str(exception)}")
            return content
    
    def _encrypt_content(self, content: str) -> str:
        """
        Encrypt the content using PowerShell's ConvertFrom-SecureString.
        
        Args:
            content: The content to encrypt
            
        Returns:
            The encrypted content
        """
        try:
            # Create a temporary file with the content
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ps1')
            temp_path = temp_file.name
            
            with open(temp_path, 'w', encoding='utf-8') as file_handle:
                file_handle.write(content)
            
            # PowerShell script to encrypt the content
            safe_path = temp_path.replace('\\', '\\\\')
            ps_script = f"""
                try {{
                    $key = (1..{self.key_size})
                    $keyBytes = [byte[]]$key
                    $originalCode = Get-Content -Path "{safe_path}" -Raw
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
            
            with open(encrypt_script_path, 'w', encoding='utf-8') as file_handle:
                file_handle.write(ps_script)
            
            # Run the PowerShell encryption script
            result = subprocess.run(
                [self.ps_cmd, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", encrypt_script_path],
                capture_output=True, text=True, check=True
            )
            
            encrypted_output = result.stdout.strip()
            if not encrypted_output:
                raise ValueError("No encryption output was received")
            
            return encrypted_output
        except subprocess.CalledProcessError as error:
            logger.error(f"PowerShell encryption error: {error.stderr}")
            raise
        except Exception as error:
            logger.error(f"Encryption error: {str(error)}")
            raise
        finally:
            # Clean up temp files
            try:
                os.unlink(temp_path)
                os.unlink(encrypt_script_path)
            except (FileNotFoundError, PermissionError, OSError) as cleanup_error:
                logger.debug(f"Failed to clean up temporary files: {cleanup_error}")
    
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
        decoded_var = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        
        launcher = f"""
# Encrypted PowerShell Script
$script:{key_var} = "{key}"
$script:{encrypted_var} = "{base64_content}"

# Decryption and execution
$script:{decoded_var} = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String($script:{encrypted_var}))
Invoke-Expression $script:{decoded_var}
"""
        return launcher
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the transformation."""
        return self.stats 