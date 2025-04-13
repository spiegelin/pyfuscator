"""
Module for configuring the obfuscation process.

This module provides configuration options for the obfuscation process.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ObfuscationConfig:
    """
    Configuration for the obfuscation process.
    
    Attributes:
        language (str): Programming language to obfuscate ('python' or 'powershell')
        common (Dict): Common configuration options
        python (Dict): Python-specific configuration options
        powershell (Dict): PowerShell-specific configuration options
        extra_options (Dict[str, Any]): Additional options for specific transformers
    """
    # Language selection
    language: str = "python"
    
    # Common options as a dictionary
    common: Dict[str, Any] = field(default_factory=lambda: {
        "remove_comments": True,
        "rename_identifiers": False,
        "junk_code": 0,
        "encrypt_layers": 0,
        "verbose": False
    })
    
    # Python-specific options
    python: Dict[str, Any] = field(default_factory=lambda: {
        "encrypt_strings": False,
        "obfuscate_imports": False,
        "dynamic_execution": False
    })
    
    # PowerShell-specific options
    powershell: Dict[str, Any] = field(default_factory=lambda: {
        "tokenize_commands": False,
        "dotnet_methods": False,
        "secure_strings": False,
        "string_divide": False,
        "base64_encode": False,
        "base64_full": False,
        "base64_commands": False,
        "script_encrypt": False,
        "use_ads": False,
        "lower_entropy": False
    })
    
    # Extra options for specific transformers
    extra_options: Dict[str, Any] = field(default_factory=dict)
    
    def get_language_config(self) -> Dict[str, Any]:
        """
        Get language-specific configuration.
        
        Returns:
            Dict[str, Any]: Dictionary with language-specific configuration
        """
        if self.language.lower() == "python":
            return {
                **self.common,
                **self.python
            }
        if self.language.lower() == "powershell":
            return {
                **self.common,
                **self.powershell
            }
        
        raise ValueError(f"Unsupported language: {self.language}")
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the configuration
        """
        return {
            "language": self.language,
            **self.common,
            **self.python,
            **self.powershell,
            "extra_options": self.extra_options
        }
        
    def __getitem__(self, key: str) -> Any:
        """
        Access configuration options as dictionary items.
        
        Args:
            key (str): Configuration option name
            
        Returns:
            Any: Configuration option value
        """
        if key in self.common:
            return self.common[key]
        if key in self.python and self.language.lower() == "python":
            return self.python[key]
        if key in self.powershell and self.language.lower() == "powershell":
            return self.powershell[key]
        if key == "language":
            return self.language
        if key == "extra_options":
            return self.extra_options
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration option with default value.
        
        Args:
            key (str): Configuration option name
            default (Any, optional): Default value if option not found. Defaults to None.
            
        Returns:
            Any: Configuration option value or default
        """
        value = self[key]
        return value if value is not None else default
