"""
Module for configuring the obfuscation process.

This module provides configuration options for the obfuscation process.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class ObfuscationConfig:
    """
    Configuration for the obfuscation process.
    
    Attributes:
        language (str): Programming language to obfuscate ('python' or 'powershell')
        remove_comments (bool): Whether to remove comments from the code
        rename_identifiers (bool): Whether to rename identifiers (variables, functions, etc.)
        encrypt_strings (bool): Whether to encrypt string literals (Python)
        obfuscate_imports (bool): Whether to obfuscate import statements (Python)
        dynamic_execution (bool): Whether to wrap function bodies with dynamic execution (Python)
        junk_code (int): Number of junk code statements to insert
        encrypt_layers (int): Number of encryption layers to apply
        tokenize_commands (bool): Whether to tokenize PowerShell commands
        dotnet_methods (bool): Whether to use .NET methods for PowerShell obfuscation
        secure_strings (bool): Whether to use SecureString for PowerShell string obfuscation
        string_divide (bool): Whether to divide strings into concatenated parts (PowerShell)
        base64_encode (bool): Whether to encode PowerShell script blocks with Base64
        base64_full (bool): Whether to encode the entire PowerShell script with Base64
        base64_commands (bool): Whether to encode individual PowerShell commands with Base64
        script_encrypt (bool): Whether to encrypt the entire PowerShell script with SecureString
        use_ads (bool): Whether to use Alternate Data Streams for PowerShell (Windows only)
        lower_entropy (bool): Whether to apply lower entropy transformation (PowerShell only)
        verbose (bool): Whether to show detailed logs and statistics
        extra_options (Dict[str, Any]): Additional options for specific transformers
    """
    # Common options
    language: str = "python"
    remove_comments: bool = True
    rename_identifiers: bool = False
    junk_code: int = 0
    encrypt_layers: int = 0
    verbose: bool = False
    
    # Python-specific options
    encrypt_strings: bool = False
    obfuscate_imports: bool = False
    dynamic_execution: bool = False
    
    # PowerShell-specific options
    tokenize_commands: bool = False
    dotnet_methods: bool = False
    secure_strings: bool = False
    string_divide: bool = False
    base64_encode: bool = False
    base64_full: bool = False
    base64_commands: bool = False
    script_encrypt: bool = False
    use_ads: bool = False
    lower_entropy: bool = False
    
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
                "remove_comments": self.remove_comments,
                "rename_identifiers": self.rename_identifiers,
                "junk_code": self.junk_code,
                "encrypt_strings": self.encrypt_strings,
                "obfuscate_imports": self.obfuscate_imports,
                "dynamic_execution": self.dynamic_execution,
                "encrypt_layers": self.encrypt_layers,
                "verbose": self.verbose,
            }
        elif self.language.lower() == "powershell":
            return {
                "remove_comments": self.remove_comments,
                "rename_identifiers": self.rename_identifiers,
                "junk_code": self.junk_code,
                "tokenize_commands": self.tokenize_commands,
                "dotnet_methods": self.dotnet_methods,
                "secure_strings": self.secure_strings,
                "string_divide": self.string_divide,
                "base64_encode": self.base64_encode,
                "base64_full": self.base64_full,
                "base64_commands": self.base64_commands,
                "script_encrypt": self.script_encrypt,
                "use_ads": self.use_ads,
                "lower_entropy": self.lower_entropy,
                "encrypt_layers": self.encrypt_layers,
                "verbose": self.verbose,
            }
        else:
            raise ValueError(f"Unsupported language: {self.language}")
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the configuration
        """
        return {
            "language": self.language,
            "remove_comments": self.remove_comments,
            "rename_identifiers": self.rename_identifiers,
            "junk_code": self.junk_code,
            "encrypt_layers": self.encrypt_layers,
            "verbose": self.verbose,
            "encrypt_strings": self.encrypt_strings,
            "obfuscate_imports": self.obfuscate_imports,
            "dynamic_execution": self.dynamic_execution,
            "tokenize_commands": self.tokenize_commands,
            "dotnet_methods": self.dotnet_methods,
            "secure_strings": self.secure_strings,
            "string_divide": self.string_divide,
            "base64_encode": self.base64_encode,
            "base64_full": self.base64_full,
            "base64_commands": self.base64_commands,
            "script_encrypt": self.script_encrypt,
            "use_ads": self.use_ads,
            "lower_entropy": self.lower_entropy,
            "extra_options": self.extra_options,
        }
        
    def __getitem__(self, key: str) -> Any:
        """
        Access configuration options as dictionary items.
        
        Args:
            key (str): Configuration option name
            
        Returns:
            Any: Configuration option value
        """
        return getattr(self, key, None)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration option with default value.
        
        Args:
            key (str): Configuration option name
            default (Any, optional): Default value if option not found. Defaults to None.
            
        Returns:
            Any: Configuration option value or default
        """
        return getattr(self, key, default)
