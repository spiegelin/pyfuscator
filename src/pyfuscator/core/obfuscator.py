"""
Core obfuscation functionality.
"""
from typing import Dict, Any

from pyfuscator.config import ObfuscationConfig
from pyfuscator.log_utils import logger, setup_logger
from pyfuscator.transformers.python.coordinator import PythonObfuscator
from pyfuscator.transformers.powershell.coordinator import PowerShellObfuscator

class Obfuscator:
    """Main obfuscator class that orchestrates the transformation process."""
    
    def __init__(self, config: ObfuscationConfig):
        """
        Initialize obfuscator with configuration.
        
        Args:
            config: Configuration for the obfuscation process
        """
        self.config = config
        self.stats = {}
        # Configure logger for this instance
        self.logger = setup_logger(verbose=self.config.get('verbose', False))
        
        # Language-specific obfuscators
        self._python_obfuscator = None
        self._powershell_obfuscator = None
        
    def obfuscate(self, source_code: str) -> str:
        """
        Execute the obfuscation process based on configuration.
        
        Args:
            source_code: The source code to obfuscate
            
        Returns:
            The obfuscated source code
        """
        # Notify about first-time operation
        if self.config.get('verbose', False):
            self.logger.info("Note: First-time obfuscation might take longer due to module initialization and processing.")
        
        # Choose processing path based on script language
        script_language = self.config.language.lower()
        
        if script_language == 'powershell':
            # Use PowerShell obfuscation process
            return self._obfuscate_powershell(source_code)
        
        # Default to Python obfuscation process
        return self._obfuscate_python(source_code)
            
    def _obfuscate_powershell(self, source: str) -> str:
        """
        Obfuscate PowerShell script content.
        
        Args:
            source: The PowerShell script content
            
        Returns:
            The obfuscated PowerShell code
        """
        if self.config.get('verbose', False):
            self.logger.info("Processing PowerShell script")
            
        # Initialize PowerShell obfuscator if not already created
        if self._powershell_obfuscator is None:
            self._powershell_obfuscator = PowerShellObfuscator(self.config)
            
        # Execute obfuscation
        obfuscated_code = self._powershell_obfuscator.obfuscate(source)
        
        # Get stats from PowerShell obfuscator
        self.stats.update(self._powershell_obfuscator.stats)
        
        self.logger.success("PowerShell obfuscation completed successfully")
        
        return obfuscated_code
        
    def _obfuscate_python(self, source: str) -> str:
        """
        Obfuscate Python script content.
        
        Args:
            source: The Python script content
            
        Returns:
            The obfuscated Python code
        """
        if self.config.get('verbose', False):
            self.logger.info("Processing Python script")
        
        # Initialize Python obfuscator if not already created
        if self._python_obfuscator is None:
            self._python_obfuscator = PythonObfuscator(self.config)
            
        # Execute obfuscation
        obfuscated_code = self._python_obfuscator.obfuscate(source)
        
        # Get stats from Python obfuscator
        self.stats.update(self._python_obfuscator.stats)
        
        self.logger.success("Python obfuscation completed successfully")
        
        return obfuscated_code

def obfuscate_file(input_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to obfuscate a file and write results to another file.
    
    Args:
        input_file: Path to the input file
        output_file: Path to the output file
        **kwargs: Additional configuration options for the obfuscator
        
    Returns:
        Dict with statistics and metadata about the obfuscation process
    """
    try:
        # Detect language if not specified
        language = kwargs.pop('language', None)
        
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Prepare config dictionaries based on the detected language
        common_options = {}
        language_specific_options = {}
        
        # Extract common options
        common_keys = ['remove_comments', 'rename_identifiers', 'junk_code', 'encrypt_layers', 'verbose']
        for key in common_keys:
            if key in kwargs:
                common_options[key] = kwargs.pop(key)
        
        # Extract language-specific options
        if language.lower() == 'python':
            python_keys = ['encrypt_strings', 'obfuscate_imports', 'dynamic_execution']
            for key in python_keys:
                if key in kwargs:
                    language_specific_options[key] = kwargs.pop(key)
        elif language.lower() == 'powershell':
            powershell_keys = [
                'tokenize_commands', 'dotnet_methods', 'secure_strings', 'string_divide',
                'base64_encode', 'base64_full', 'base64_commands', 'script_encrypt',
                'use_ads', 'lower_entropy'
            ]
            for key in powershell_keys:
                if key in kwargs:
                    language_specific_options[key] = kwargs.pop(key)
        
        # Create ObfuscationConfig
        config = ObfuscationConfig(language=language)
        
        # Update the config dictionaries
        config.common.update(common_options)
        if language.lower() == 'python':
            config.python.update(language_specific_options)
        elif language.lower() == 'powershell':
            config.powershell.update(language_specific_options)
        
        # Any remaining kwargs go into extra_options
        config.extra_options.update(kwargs)
        
        # Create obfuscator
        obfuscator = Obfuscator(config)
        
        # Execute obfuscation
        obfuscated_code = obfuscator.obfuscate(source_code)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(obfuscated_code)
        
        # Return statistics
        return {
            'stats': obfuscator.stats
        }
    except Exception as e:
        logger.error(f"Error in obfuscate_file: {str(e)}")
        raise