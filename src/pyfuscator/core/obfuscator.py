"""
Core obfuscation functionality.
"""
import ast
import astunparse
import random
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from pyfuscator.config import ObfuscationConfig
from pyfuscator.core.utils import (
    remove_comments, fix_slice_syntax, set_parent_nodes
)
from pyfuscator.core.globals import IMPORT_ALIASES, IMPORT_MAPPING
from pyfuscator.encryption.methods import (
    encryption_method_1, encryption_method_2, 
    encryption_method_3, encryption_method_4
)
from pyfuscator.log_utils import logger, setup_logger
from pyfuscator.transformers.python.imports import (
    ImportTracker, ObfuscateImports, ReplaceImportNames
)
from pyfuscator.transformers.python.identifiers import RenameIdentifiers, ImportRenamer
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
        script_language = self.config.language.lower() if hasattr(self.config, 'language') else 'python'
        
        if script_language == 'powershell':
            # Use PowerShell obfuscation process
            return self._obfuscate_powershell(source_code)
        else:
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
        if self.config.verbose:
            self.logger.info("Processing PowerShell script")
            
        # Create PowerShell obfuscator and transform content
        ps_obfuscator = PowerShellObfuscator(self.config)
        obfuscated_code = ps_obfuscator.obfuscate(source)
        
        # Get stats from PowerShell obfuscator if available
        if hasattr(ps_obfuscator, 'stats'):
            self.stats.update(ps_obfuscator.stats)
        
        # Get rename map from PowerShell obfuscator if available and identifier renaming was enabled
        if hasattr(self.config, 'rename_identifiers') and self.config.rename_identifiers:
            # If the identifier renamer exists in the coordinator, get its map
            if hasattr(ps_obfuscator, 'identifier_renamer') and ps_obfuscator.identifier_renamer:
                self.stats['rename_map'] = ps_obfuscator.identifier_renamer.map_tracker
            
        # Log success message for each enabled technique
        if hasattr(self.config, 'rename_identifiers') and self.config.rename_identifiers:
            self.logger.success("Renamed identifiers in PowerShell script")
            
        if hasattr(self.config, 'encrypt_strings') and self.config.encrypt_strings:
            self.logger.success("Obfuscated strings in PowerShell script")
            
        if hasattr(self.config, 'tokenize_commands') and self.config.tokenize_commands:
            self.logger.success("Tokenized commands in PowerShell script")
            
        if hasattr(self.config, 'dotnet_methods') and self.config.dotnet_methods:
            self.logger.success("Applied .NET method obfuscation in PowerShell script")
            
        if hasattr(self.config, 'junk_code') and self.config.junk_code > 0:
            self.logger.success(f"Added {self.config.junk_code} junk statements")
            
        if hasattr(self.config, 'lower_entropy') and self.config.lower_entropy:
            self.logger.success("Applied lower entropy transformation to PowerShell script")
            
        if hasattr(self.config, 'encrypt_layers') and self.config.encrypt_layers > 0:
            self.logger.success(f"Applied {self.config.encrypt_layers} layers of encoding")
        
        self.logger.success(f"PowerShell obfuscation completed successfully")
        
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
        # This is just a tracking step and doesn't transform the code
        if self.config.get('rename_identifiers', False) or self.config.get('obfuscate_imports', False):
            if self.config.get('verbose', False):
                self.logger.info("Tracking imports for renaming/obfuscation")
            import_tracker = ImportTracker()
            import_tracker.visit(tree)
            if self.config.get('verbose', False):
                self.logger.info(f"Found imports to track in the code")

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
            
            # Log success
            self.logger.success(f"Renamed {self.stats['identifiers_renamed']} identifiers")

        # Store the rename map in the stats for later display
        self.stats['rename_map'] = rename_map
        
        # Apply string encryption if specified
        if self.config.get('encrypt_strings', False):
            if self.config.get('verbose', False):
                self.logger.info("Encrypting string literals")
                
            encrypt_transformer = EncryptStrings()  # Use default settings
            tree = encrypt_transformer.visit(tree)
            
            # Get stats
            self.stats['strings_encrypted'] = getattr(encrypt_transformer, 'strings_encrypted', 0)
            
            # Log success
            self.logger.success(f"Encrypted {self.stats['strings_encrypted']} string literals")

        # Apply dynamic function execution if specified
        if self.config.get('dynamic_execution', False):
            if self.config.get('verbose', False):
                self.logger.info("Converting functions to dynamic execution")
                
            dynamic_transformer = DynamicFunctionBody()
            tree = dynamic_transformer.visit(tree)
            
            # Get stats
            self.stats['functions_dynamic'] = getattr(dynamic_transformer, 'functions_wrapped', 0)
            
            # Log success
            self.logger.success(f"Applied dynamic execution to {self.stats['functions_dynamic']} functions")

        # Convert the AST back to source code
        if self.config.get('verbose', False):
            self.logger.info("Converting AST back to source code")
            
        result = astunparse.unparse(tree)
        
        # Fix slice syntaxes as astunparse can incorrectly format them
        result = fix_slice_syntax(result)

        # Apply encryption layers if specified
        if self.config.get('encrypt_layers', 0) > 0:
            layers = self.config.get('encrypt_layers', 0)
            if self.config.get('verbose', False):
                self.logger.info(f"Applying {layers} encryption layers")
                
            # Apply encryption layers with different methods based on layer count
            if layers >= 1:
                result = encryption_method_1(result)
            if layers >= 2:
                result = encryption_method_2(result)
            if layers >= 3:
                result = encryption_method_3(result)
            if layers >= 4:
                result = encryption_method_4(result)
            # Layer 5 is a combination of all methods
            if layers >= 5:
                result = encryption_method_1(encryption_method_2(encryption_method_3(encryption_method_4(result))))
                
            # Log success
            self.logger.success(f"Applied {layers} layers of encryption")
            
            # Update stats
            self.stats['encryption_layers'] = layers
            
        # Return the obfuscated source
        return result

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
        if not language:
            language = detect_script_language(input_file)
        
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Create ObfuscationConfig
        config = ObfuscationConfig(language=language, **kwargs)
        
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

def detect_script_language(input_file: str, specified_language: Optional[str] = None) -> str:
    """
    Detect the script language based on file extension or use the specified language.
    
    Args:
        input_file: Path to the input file
        specified_language: Language specified by the user (if any)
        
    Returns:
        Detected or specified script language
    """
    from pathlib import Path
    
    if specified_language:
        # User specified a language
        logger.info(f"Using specified script language: {specified_language}")
        script_language = specified_language
    else:
        # Auto-detect based on file extension
        file_ext = Path(input_file).suffix.lower()
        
        if file_ext == '.py':
            script_language = 'python'
            logger.info(f"Auto-detected Python script based on .py extension")
        elif file_ext in ['.ps1', '.psm1', '.psd1']:
            script_language = 'powershell'
            logger.info(f"Auto-detected PowerShell script based on {file_ext} extension")
        else:
            logger.warning(f"Could not determine script language from extension {file_ext}")
            logger.warning(f"Defaulting to Python. Use -x flag to specify script language explicitly.")
            script_language = 'python'  # Default to Python for now
    
    return script_language 