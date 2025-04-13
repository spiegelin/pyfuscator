"""
Core obfuscation functionality.
"""
import random
from typing import Dict, Any
import ast
import astunparse

from pyfuscator.config import ObfuscationConfig
from pyfuscator.core.utils import (
    remove_comments, fix_slice_syntax, set_parent_nodes
)
from pyfuscator.core.globals import IMPORT_ALIASES, IMPORT_MAPPING
from pyfuscator.encryption.methods import (
    encryption_method_1, encryption_method_2, 
    encryption_method_3, encryption_method_4,
    encryption_method_5
)
from pyfuscator.log_utils import logger, setup_logger
from pyfuscator.transformers.python.imports import (
    ImportTracker, ObfuscateImports, ReplaceImportNames
)
from pyfuscator.transformers.python.identifiers import RenameIdentifiers
from pyfuscator.transformers.python.strings import EncryptStrings
from pyfuscator.transformers.python.functions import DynamicFunctionBody
from pyfuscator.transformers.python.junk import InsertJunkCode
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
            self.logger.info("Note: First-time obfuscation might take longer due to module initialization and AST processing.")
        
        # Clear global state
        IMPORT_ALIASES.clear()
        IMPORT_MAPPING.clear()
        
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
            
        # Create PowerShell obfuscator and transform content
        ps_obfuscator = PowerShellObfuscator(self.config)
        obfuscated_code = ps_obfuscator.obfuscate(source)
        
        # Get stats from PowerShell obfuscator if available
        if hasattr(ps_obfuscator, 'stats'):
            self.stats.update(ps_obfuscator.stats)
        
        # Get rename map from PowerShell obfuscator if available and identifier renaming was enabled
        if self.config.get('rename_identifiers', False):
            # If the identifier renamer exists in the coordinator, get its map
            if hasattr(ps_obfuscator, 'identifier_renamer') and ps_obfuscator.identifier_renamer:
                self.stats['rename_map'] = ps_obfuscator.identifier_renamer.map_tracker
            
        # Log success message for each enabled technique
        if self.config.get('rename_identifiers', False):
            self.logger.success("Renamed identifiers in PowerShell script")
            
        if self.config.get('secure_strings', False):
            self.logger.success("Obfuscated strings in PowerShell script")
            
        if self.config.get('tokenize_commands', False):
            self.logger.success("Tokenized commands in PowerShell script")
            
        if self.config.get('dotnet_methods', False):
            self.logger.success("Applied .NET method obfuscation in PowerShell script")
            
        if self.config.get('junk_code', 0) > 0:
            self.logger.success(f"Added {self.config.get('junk_code')} junk statements")
            
        if self.config.get('lower_entropy', False):
            self.logger.success("Applied lower entropy transformation to PowerShell script")
            
        if self.config.get('encrypt_layers', 0) > 0:
            self.logger.success(f"Applied {self.config.get('encrypt_layers')} layers of encoding")
        
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
        # Remove comments always (as AST will remove them anyway)
        # Only log the action if the flag is explicitly set and in verbose mode
        if self.config.get('remove_comments', True) and self.config.get('verbose', False):
            self.logger.info("Removing comments and docstrings")
        source_before = len(source)
        source = remove_comments(source)
        source_after = len(source)
        
        # Always log success for comment removal, as it's a default action
        self.logger.success("Removed comments and docstrings")
                
        # Update stats for comment removal
        self.stats['removed_comment_count'] = 1  # Simplified count
        self.stats['removed_comment_chars'] = source_before - source_after

        # Parse source into AST
        if self.config.get('verbose', False):
            self.logger.info("Parsing source into AST")
        tree = ast.parse(source)
        
        # Set parent nodes for docstring detection
        # This is just a helper step and doesn't transform the code
        if self.config.get('verbose', False):
            self.logger.info("Setting parent nodes for AST")
        set_parent_nodes(tree)

        # Track imports if we need them (for identifier renaming or import obfuscation)
        if self.config.get('rename_identifiers', False) or self.config.get('obfuscate_imports', False):
            if self.config.get('verbose', False):
                self.logger.info("Tracking imports for renaming/obfuscation")
            import_tracker = ImportTracker()
            import_tracker.visit(tree)
            if self.config.get('verbose', False):
                self.logger.info("Found imports to track in the code")

        # Variable to store the rename map
        rename_map = {}
            
        # Apply identifier renaming if specified
        if self.config.get('rename_identifiers', False):
            if self.config.get('verbose', False):
                self.logger.info("Renaming variables, functions, and class names")
                
            # Create the transformer with import awareness
            rename_transformer = RenameIdentifiers(import_aware=True)
            tree = rename_transformer.visit(tree)
            
            # Get stats
            self.stats['identifiers_renamed'] = len(rename_transformer.mapping)
            
            # Store the rename map for display
            rename_map = rename_transformer.map_tracker
            self.stats['rename_map'] = rename_map
            
            # Log success
            self.logger.success(f"Renamed {self.stats['identifiers_renamed']} identifiers")

        # Apply junk code if specified
        if self.config.get('junk_code', 0) > 0:
            junk_count = self.config.get('junk_code', 0)
            if self.config.get('verbose', False):
                self.logger.info(f"Inserting {junk_count} junk code statements")
            
            # Apply the junk code transformer
            junk_transformer = InsertJunkCode(
                num_statements=junk_count, 
                pep8_compliant=True,
                junk_at_end=True,
                verbose=self.config.get('verbose', False)
            )
            tree = junk_transformer.visit(tree)
            
            # Get actual number of statements added
            actual_count = getattr(junk_transformer, 'total_statements_added', junk_count)
            self.stats['junk_statements'] = actual_count
            
            # Success message
            self.logger.success(f"Added {actual_count} junk statements")

        # Apply import obfuscation if specified
        if self.config.get('obfuscate_imports', False):
            if self.config.get('verbose', False):
                self.logger.info("Obfuscating import statements")
                self.logger.info("Replacing original import names with aliases")
            
            obfuscate_imports = ObfuscateImports()
            tree = obfuscate_imports.visit(tree)
            
            replace_imports = ReplaceImportNames()
            tree = replace_imports.visit(tree)
            
            # Update stats
            self.stats['imports_obfuscated'] = len(IMPORT_ALIASES)
            self.stats['import_aliases'] = len(IMPORT_MAPPING)
            
            # Log success
            self.logger.success(f"Obfuscated {self.stats['imports_obfuscated']} import statements")

        
        # Apply string encryption if specified
        if self.config.get('encrypt_strings', False):
            if self.config.get('verbose', False):
                self.logger.info("Encrypting string literals")
                
            # Create the transformer
            string_transformer = EncryptStrings()
            tree = string_transformer.visit(tree)
            
            # Get stats
            self.stats['strings_encrypted'] = getattr(string_transformer, 'strings_encrypted', 0)
            
            # Log success
            self.logger.success(f"Encrypted {self.stats['strings_encrypted']} string literals")

        # Apply dynamic execution if specified
        if self.config.get('dynamic_execution', False):
            if self.config.get('verbose', False):
                self.logger.info("Applying dynamic function execution")
                
            # Create the transformer
            dynamic_transformer = DynamicFunctionBody()
            tree = dynamic_transformer.visit(tree)
            
            # Get stats
            self.stats['functions_dynamic'] = getattr(dynamic_transformer, 'count', 0)
            
            # Log success
            self.logger.success(f"Applied dynamic execution to {self.stats['functions_dynamic']} functions")

        # Convert AST back to source code
        result = astunparse.unparse(tree)
        
        # Fix slice syntax issues that astunparse can cause
        if self.config.get('verbose', False):
            self.logger.info("Fixing slice syntax issues")
        result = fix_slice_syntax(result)
        
        # Apply encryption if specified
        encryption_layers = self.config.get('encrypt_layers', 0)
        if encryption_layers > 0:
            if self.config.get('verbose', False):
                self.logger.info(f"Applying {encryption_layers} layers of encryption")
            
            # Apply specified number of encryption layers
            result = self._apply_encryption_layers(result, encryption_layers)
            
            # Update stats
            self.stats['encryption_layers'] = encryption_layers
            
            # Log success
            self.logger.success(f"Applied {encryption_layers} layers of encryption")
        
        # Return the final transformed code
        return result

    def _apply_encryption_layers(self, code: str, layers: int) -> str:
        """
        Apply multiple layers of encryption to code.
        
        Args:
            code: The code to encrypt
            layers: Number of encryption layers to apply
            
        Returns:
            Encrypted code
        """
        for i in range(layers):
            method = random.randint(1, 5)
            method_name = ["Linear Congruence","XOR with Shuffle Key","RSA-like","Key Array XOR","Triple Layer Cipher"]
            if self.config.get('verbose', False):
                self.logger.info(f"Applying encryption method {method_name[method-1]} (layer {i+1}/{layers})")
            
            if method == 1:
                code = encryption_method_1(code)
            elif method == 2:
                code = encryption_method_2(code)
            elif method == 3:
                code = encryption_method_3(code)
            elif method == 4:
                code = encryption_method_4(code)
            else:
                code = encryption_method_5(code)
            
            if self.config.get('verbose', False):
                self.logger.info(f"Layer {i+1} encryption complete, code size: {len(code)} bytes")
            
        return code

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