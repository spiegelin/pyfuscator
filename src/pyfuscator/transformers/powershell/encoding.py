"""
PowerShell encoding/decoding transformer.
"""
import re
import base64
import random
import subprocess
import os
import tempfile
import textwrap
import platform
from typing import List, Tuple, Dict, Any, Optional

from pyfuscator.log_utils import logger

class EncodeCommands:
    """Transformer that encodes PowerShell commands and script blocks."""
    
    def __init__(self, encode_blocks: bool = True, encode_full: bool = False, secure_string: bool = False):
        """
        Initialize the transformer.
        
        Args:
            encode_blocks: Whether to encode individual script blocks
            encode_full: Whether to encode the entire script (only if no blocks are encoded)
            secure_string: Whether to use SecureString for encryption (stronger than base64)
        """
        self.encode_blocks = encode_blocks
        self.encode_full = encode_full
        self.secure_string = secure_string
        self.count = 0  # Track number of blocks encoded
        self._ps_cmd = "powershell" if platform.system() == "Windows" else "pwsh"
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by encoding commands and blocks.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with encoded commands
        """
        self.count = 0
        
        if not content.strip():
            return content
            
        if self.secure_string:
            # Use SecureString encryption for the entire script
            logger.info("Encrypting PowerShell script using SecureString")
            return self._encrypt_with_secure_string(content)
        elif self.encode_blocks:
            # Find script blocks: { ... }
            # This is a simplified pattern - complex blocks may need more sophisticated parsing
            block_pattern = r'(?<!\$)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
            
            def encode_block(match):
                """Encode a script block."""
                # Skip empty blocks or blocks with special constructs
                block_content = match.group(1).strip()
                if not block_content or '{' in block_content or '}' in block_content:
                    return match.group(0)
                    
                self.count += 1
                # Choose an encoding technique
                technique = random.choice([
                    self._encode_base64,
                    self._encode_compressed
                ])
                
                return technique(block_content)
            
            transformed = re.sub(block_pattern, encode_block, content)
            logger.info(f"Encoded {self.count} script blocks in PowerShell script")
            return transformed
        elif self.encode_full and not self.encode_blocks:
            # Encode the entire script
            logger.info("Encoding entire PowerShell script")
            return self._encode_full_script(content)
        else:
            return content
    
    def _encrypt_with_secure_string(self, script: str) -> str:
        """
        Encrypt a script using PowerShell's SecureString functionality with a fixed key.
        
        Args:
            script: Script content to encrypt
            
        Returns:
            PowerShell script that decrypts and executes the encrypted content
        """
        # Create temporary file for the script
        with tempfile.NamedTemporaryFile(suffix='.ps1', delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(script)
            temp_path = temp_file.name
        
        try:
            # PowerShell script to encrypt the content
            ps_script = textwrap.dedent(f'''
                try {{
                    $key = (1..32)
                    $keyBytes = [byte[]]$key
                    $originalCode = Get-Content -Path "{temp_path}" -Raw
                    $secure = ConvertTo-SecureString $originalCode -AsPlainText -Force
                    $encrypted = ConvertFrom-SecureString -SecureString $secure -Key $keyBytes
                    Write-Output $encrypted
                }} catch {{
                    Write-Error "Error: $($_.Exception.Message)"
                    exit 1
                }}
            ''')
            
            try:
                # Execute PowerShell to encrypt the script
                result = subprocess.run([self._ps_cmd, "-NoProfile", "-NonInteractive", "-Command", ps_script],
                                      capture_output=True, text=True, check=True)
                encrypted_output = result.stdout.strip()
                
                if not encrypted_output:
                    logger.error("No encryption output was received")
                    return script  # Fall back to original script
                
                # Generate the loader script
                loader = textwrap.dedent(f'''\
                    # Self-decrypting PowerShell script loader
                    # The key must be the same as the one used during encryption
                    $key = [byte[]](1..32)
                    
                    # Encrypted payload (generated using ConvertFrom-SecureString)
                    $encryptedScript = @"
{encrypted_output}
"@
                    
                    try {{
                        # Convert the encrypted string back into a SecureString
                        $secureString = ConvertTo-SecureString -String $encryptedScript -Key $key
                        # Extract the plain-text string
                        $plainText = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString)
                        )
                        # Execute the decrypted script
                        Invoke-Expression $plainText
                    }} catch {{
                        Write-Error "Decryption or execution error: $($_.Exception.Message)"
                        exit 1
                    }}
                ''')
                
                return loader
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Error executing PowerShell to encrypt: {e.stderr}")
                return script  # Fall back to original script
            except Exception as e:
                logger.error(f"Error during encryption: {str(e)}")
                return script  # Fall back to original script
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _encode_base64(self, script: str) -> str:
        """
        Encode a script segment using Base64.
        
        Args:
            script: Script content to encode
            
        Returns:
            PowerShell command that decodes and executes the script
        """
        # Convert to bytes and encode
        script_bytes = script.encode('utf-16le')
        encoded = base64.b64encode(script_bytes).decode('ascii')
        
        # Generate PowerShell commands to decode and execute
        decoder = f"[System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded}'))"
        executor = f"Invoke-Expression ({decoder})"
        
        return executor
    
    def _encode_compressed(self, script: str) -> str:
        """
        Encode a script segment using compression and Base64.
        
        Args:
            script: Script content to encode
            
        Returns:
            PowerShell command that decompresses, decodes and executes the script
        """
        # For this example, we'll use a simplified version without actual compression
        # In a real implementation, you would compress the script first
        script_bytes = script.encode('utf-16le')
        encoded = base64.b64encode(script_bytes).decode('ascii')
        
        # Generate PowerShell commands to decompress, decode and execute
        decoder = (
            "$data = [System.Convert]::FromBase64String('{0}'); "
            "$ms = New-Object System.IO.MemoryStream; "
            "$ms.Write($data, 0, $data.Length); "
            "$ms.Seek(0,0) | Out-Null; "
            "$sr = New-Object System.IO.StreamReader($ms, [System.Text.Encoding]::Unicode); "
            "$decoded = $sr.ReadToEnd(); "
            "Invoke-Expression $decoded"
        ).format(encoded)
        
        return f"& {{{decoder}}}"
    
    def _encode_full_script(self, script: str) -> str:
        """
        Encode the entire script.
        
        Args:
            script: Full script content to encode
            
        Returns:
            PowerShell launcher script that decodes and executes the original script
        """
        # Convert to bytes and encode
        script_bytes = script.encode('utf-16le')
        encoded = base64.b64encode(script_bytes).decode('ascii')
        
        # Create a launcher script that decodes and executes the encoded content
        launcher = (
            "# PowerShell Obfuscated Script\n"
            "# Generated by PyFuscator\n\n"
            "$scriptEncoded = '{0}'\n"
            "$scriptBytes = [System.Convert]::FromBase64String($scriptEncoded)\n"
            "$scriptText = [System.Text.Encoding]::Unicode.GetString($scriptBytes)\n"
            "Invoke-Expression $scriptText"
        ).format(encoded)
        
        return launcher
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the transformation.
        
        Returns:
            Dict with transformation statistics
        """
        return {
            "blocks_encoded": self.count
        } 