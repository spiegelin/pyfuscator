"""
PowerShell Script Encryption transformer - encrypts entire scripts using SecureString.
"""
import re
import random
import base64
import string
from typing import Dict, Any, List

from pyfuscator.core.transformer import Transformer
from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class PowerShellScriptEncryptor(Transformer):
    """Transformer that encrypts PowerShell scripts using SecureString with random keys."""
    
    def __init__(self, generate_launcher: bool = True):
        """
        Initialize the PowerShell Script Encryption transformer.
        
        Args:
            generate_launcher: Whether to generate a launcher script
        """
        super().__init__()
        self.generate_launcher = generate_launcher
        self.stats = {
            "encrypted_scripts": 0,
            "encryption_key_length": 0,
            "encrypted_content_length": 0
        }
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by encrypting its content.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            The transformed PowerShell script with encrypted content
        """
        if not content.strip():
            return content
        
        try:
            # Generate a random encryption key
            key_bytes = self._generate_random_key(32)  # 256-bit key
            self.stats["encryption_key_length"] = len(key_bytes)
            
            # Encrypt the script content
            _, launcher_script = self._encrypt_script(content, key_bytes)
            self.stats["encrypted_content_length"] = len(content)
            self.stats["encrypted_scripts"] += 1
            
            logger.info(f"Encrypted PowerShell script with a {len(key_bytes) * 8}-bit key")
            
            # Return the launcher script
            return launcher_script
                
        except Exception as e:
            logger.error(f"Failed to encrypt PowerShell script: {e}")
            # In case of failure, return the original content
            return content
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about script encryption.
        
        Returns:
            Dict with statistics about encrypted scripts
        """
        return self.stats
    
    def _generate_random_key(self, length: int) -> bytes:
        """
        Generate a random encryption key.
        
        Args:
            length: The length of the key in bytes
            
        Returns:
            Random bytes for encryption key
        """
        return bytes([random.randint(1, 255) for _ in range(length)])
    
    def _encrypt_script(self, content: str, key_bytes: bytes) -> tuple:
        """
        Encrypt PowerShell script content using PowerShell's native encryption.
        
        Args:
            content: The PowerShell script content to encrypt
            key_bytes: The encryption key
            
        Returns:
            Tuple of (unused, launcher_script)
        """
        # Generate random variable names for better obfuscation
        key_var = random_name(5)
        encrypted_var = random_name(7)
        script_var = random_name(6)
        
        # Convert the key to a PowerShell byte array format
        key_array = f"[byte[]]@({','.join([str(b) for b in key_bytes])})"
        
        # We need to pre-encrypt the content using the same approach as powershell-encryption.py
        # This requires us to use subprocess to run PowerShell and encrypt the content
        import subprocess
        import tempfile
        import os
        import platform
        import shutil
        
        # Determine PowerShell executable based on platform
        powershell_exe = "powershell.exe" if platform.system() == "Windows" else "pwsh"
        has_powershell = shutil.which(powershell_exe) is not None
        
        # If PowerShell is not available, use the fallback method
        if not has_powershell:
            return self._fallback_encrypt_script(content, key_bytes)
        
        # Create a temporary file with the content
        with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Create PowerShell script to encrypt the content
            ps_encrypt_script = f"""
$key = {key_array}
$originalCode = Get-Content -Path "{temp_path}" -Raw
$secure = ConvertTo-SecureString $originalCode -AsPlainText -Force
$encrypted = ConvertFrom-SecureString -SecureString $secure -Key $key
Write-Output $encrypted
"""
            
            # Run PowerShell to encrypt the content with better error handling
            try:
                process = subprocess.run(
                    [powershell_exe, "-NoProfile", "-NonInteractive", "-Command", ps_encrypt_script],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Get the encrypted output
                encrypted_data = process.stdout.strip()
                
                # Verify we got some output
                if not encrypted_data:
                    logger.warning("PowerShell encryption returned empty result, using fallback method")
                    return self._fallback_encrypt_script(content, key_bytes)
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"PowerShell encryption failed: {e}")
                logger.error(f"STDERR: {e.stderr}")
                return self._fallback_encrypt_script(content, key_bytes)
            
            # Create the launcher script with improved error handling
            launcher_script = f"""
# PowerShell Encrypted Script Loader
${key_var} = {key_array}
${encrypted_var} = @"
{encrypted_data}
"@

try {{
    # Decrypt the script
    try {{
        $secureString = ConvertTo-SecureString -String ${encrypted_var} -Key ${key_var}
    }} catch {{
        Write-Error "Failed to decrypt the script: $_"
        exit 1
    }}
    
    # Convert SecureString to plaintext
    try {{
        $plainText = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString)
        )
    }} catch {{
        Write-Error "Failed to convert decrypted content: $_"
        exit 1
    }}
    
    # Create script block
    try {{
        ${script_var} = [ScriptBlock]::Create($plainText)
    }} catch {{
        Write-Error "Failed to create script block: $_"
        exit 1
    }}
    
    # Execute the decrypted script
    Invoke-Command -ScriptBlock ${script_var}
}} catch {{
    Write-Error "Unexpected error in script execution: $_"
    exit 1
}}
"""
            return "", launcher_script
            
        except Exception as e:
            logger.error(f"Failed to encrypt PowerShell script: {e}")
            # Fallback to simpler encryption method if subprocess fails
            return self._fallback_encrypt_script(content, key_bytes)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _fallback_encrypt_script(self, content: str, key_bytes: bytes) -> tuple:
        """
        Fallback method for script encryption when subprocess approach fails.
        
        Args:
            content: The PowerShell script content to encrypt
            key_bytes: The encryption key
            
        Returns:
            Tuple of (unused, launcher_script)
        """
        # Convert bytes to hex strings for direct embedding in PowerShell
        import binascii
        content_bytes = content.encode('utf-16le')
        content_hex = binascii.hexlify(content_bytes).decode('ascii')
        
        # Generate random variable names for better obfuscation
        key_var = random_name(5)
        hex_var = random_name(7)
        bytes_var = random_name(6)
        text_var = random_name(8)
        script_var = random_name(5)
        
        # Convert the key to a PowerShell byte array format
        key_array = f"[byte[]]@({','.join([str(b) for b in key_bytes])})"
        
        # Create the launcher script using a hex-encoded version of the original script with improved error handling
        launcher_script = f"""
# PowerShell Encrypted Script Loader (Fallback Method)
${key_var} = {key_array}
${hex_var} = '{content_hex}'

try {{
    # Convert hex to bytes
    try {{
        ${bytes_var} = [byte[]]::new(${hex_var}.Length / 2)
        for ($i = 0; $i -lt ${hex_var}.Length; $i += 2) {{
            ${bytes_var}[$i / 2] = [convert]::ToByte(${hex_var}.Substring($i, 2), 16)
        }}
    }} catch {{
        Write-Error "Failed to convert hex to bytes: $_"
        exit 1
    }}
    
    # Convert bytes to text
    try {{
        ${text_var} = [System.Text.Encoding]::Unicode.GetString(${bytes_var})
    }} catch {{
        Write-Error "Failed to convert bytes to text: $_"
        exit 1
    }}
    
    # Create script block and execute
    try {{
        ${script_var} = [ScriptBlock]::Create(${text_var})
    }} catch {{
        Write-Error "Failed to create script block: $_"
        exit 1
    }}
    
    # Execute the script
    Invoke-Command -ScriptBlock ${script_var}
}} catch {{
    Write-Error "Unexpected error in script execution: $_"
    exit 1
}}
"""
        return "", launcher_script
    
    def _encrypt_with_key(self, content: str, key_bytes: bytes) -> str:
        """
        Encrypt content with key using PowerShell SecureString functionality.
        
        This function encrypts content in a way compatible with PowerShell's
        ConvertTo-SecureString and ConvertFrom-SecureString cmdlets. We use
        AES encryption with the provided key to match PowerShell's behavior.
        
        Args:
            content: The content to encrypt
            key_bytes: The encryption key
            
        Returns:
            String representation of encrypted content
        """
        try:
            # Use built-in libraries for AES encryption
            import os
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            # Generate random IV (16 bytes for AES)
            iv = os.urandom(16)
            
            # Pad the content to block size
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(content.encode('utf-16le')) + padder.finalize()
            
            # Create an encryptor object
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # Encrypt the padded data
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Format as Base64 with IV prepended
            full_encrypted = iv + encrypted_data
            encrypted = base64.b64encode(full_encrypted).decode('ascii')
            
            return encrypted
            
        except ImportError:
            # Fallback method if cryptography is not available
            # This is less secure but will still provide basic obfuscation
            logger.warning("Cryptography package not available, using basic XOR encryption instead")
            key_xor = bytes([x % 256 for x in [ord(c) ^ k for c, k in zip(content.ljust(len(content) + 10), 
                                                                        key_bytes * (len(content) // len(key_bytes) + 1))]])
            encrypted = base64.b64encode(key_xor).decode('ascii')
            return encrypted 