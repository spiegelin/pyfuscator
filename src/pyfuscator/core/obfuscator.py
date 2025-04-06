"""
Core obfuscation functionality.
"""
import ast
import astunparse
import random
from typing import Dict, Any, Optional, List, Union

from pyfuscator.config import ObfuscationConfig
from pyfuscator.core.utils import (
    remove_comments, fix_slice_syntax, set_parent_nodes
)
from pyfuscator.core.globals import IMPORT_ALIASES, IMPORT_MAPPING
from pyfuscator.encryption.methods import (
    encryption_method_1, encryption_method_2, 
    encryption_method_3, encryption_method_4
)
from pyfuscator.log_utils import logger
from pyfuscator.transformers.imports import (
    ImportTracker, ObfuscateImports, ReplaceImportNames
)
from pyfuscator.transformers.identifiers import RenameIdentifiers, ImportRenamer
from pyfuscator.transformers.strings import EncryptStrings
from pyfuscator.transformers.functions import DynamicFunctionBody
from pyfuscator.transformers.junk import InsertJunkCode

class Obfuscator:
    """Main obfuscator class that orchestrates the transformation process."""
    
    def __init__(self, config: ObfuscationConfig):
        """
        Initialize obfuscator with configuration.
        
        Args:
            config: Configuration for the obfuscation process
        """
        self.config = config
        
    def obfuscate(self) -> None:
        """
        Execute the obfuscation process based on configuration.
        """
        # Notify about first-time operation
        logger.info("Note: First-time obfuscation might take longer due to module initialization and AST processing.")
        
        # Clear global state
        IMPORT_ALIASES.clear()
        IMPORT_MAPPING.clear()
        
        # Apply all techniques if specified
        if self.config.all_techniques:
            self.config.apply_all_techniques()
            if self.config.verbose:
                logger.info("All obfuscation techniques enabled")
            
        # Read input file
        logger.info(f"Reading input file: {self.config.input_file}")
        
        with open(self.config.input_file, "r", encoding="utf-8") as f:
            source = f.read()
            if self.config.verbose:
                logger.info(f"Successfully read {len(source)} bytes from input file")

        # Remove comments always (as AST will remove them anyway)
        # Only log the action if the flag is explicitly set and in verbose mode
        if self.config.remove_comments and self.config.verbose:
            logger.info("Removing comments and docstrings")
        source_before = len(source)
        source = remove_comments(source)
        source_after = len(source)
        if self.config.verbose:
            logger.info(f"Removed {source_before - source_after} bytes of comments and whitespace")
            if self.config.remove_comments:
                logger.success("Removed comments and docstrings")

        # Parse source into AST
        logger.info("Parsing source into AST") if self.config.verbose else None
        tree = ast.parse(source, filename=self.config.input_file)
        
        # Set parent nodes for docstring detection
        # This is just a helper step and doesn't transform the code
        logger.info("Setting parent nodes for AST") if self.config.verbose else None
        set_parent_nodes(tree)

        # Track imports if we need them (for identifier renaming or import obfuscation)
        # This is just a tracking step and doesn't transform the code
        if self.config.identifier_rename or self.config.obfuscate_imports:
            if self.config.verbose:
                logger.info("Tracking imports for renaming/obfuscation")
            import_tracker = ImportTracker()
            import_tracker.visit(tree)
            if self.config.verbose:
                logger.info(f"Found imports to track in the code")

        # Apply junk code if specified
        if self.config.junk_code > 0:
            if self.config.verbose:
                logger.info(f"Inserting {self.config.junk_code} junk code statements")
            
            # Apply the junk code transformer
            junk_transformer = InsertJunkCode(
                num_statements=self.config.junk_code, 
                pep8_compliant=True,
                junk_at_end=True,
                verbose=self.config.verbose
            )
            tree = junk_transformer.visit(tree)
            
            # Get actual number of statements added
            actual_count = getattr(junk_transformer, 'total_statements_added', self.config.junk_code)
            
            # Use success instead of info for reporting completed actions
            if self.config.verbose:
                logger.success(f"Added {actual_count} junk statements")

        # Apply import obfuscation if specified
        if self.config.obfuscate_imports:
            if self.config.verbose:
                logger.info("Obfuscating import statements")
                logger.info("Replacing original import names with aliases")
            tree = ObfuscateImports().visit(tree)
            tree = ReplaceImportNames().visit(tree)
            if self.config.verbose:
                logger.success(f"Obfuscated import statements")
            
        # Apply identifier renaming if specified
        if self.config.identifier_rename:
            # Only use import-aware mode if import obfuscation is also enabled
            import_aware = self.config.obfuscate_imports
            if self.config.verbose:
                logger.info("Renaming identifiers" + (" (with import tracking)" if not import_aware else ""))
            
            rename_identifiers = RenameIdentifiers(import_aware=import_aware)
            tree = rename_identifiers.visit(tree)
            
            # Only rename imports separately if we're not already obfuscating imports
            if not self.config.obfuscate_imports:
                logger.info("Renaming import statements") if self.config.verbose else None
                tree = ImportRenamer(rename_identifiers.import_mapping).visit(tree)
                
            if self.config.verbose:
                count = len(rename_identifiers.import_mapping)
                logger.info(f"Successfully renamed {count} identifiers")
                logger.success(f"Renamed identifiers")
        
        # Apply string encryption if enabled
        if self.config.encrypt_strings:
            if self.config.verbose:
                logger.info("Encrypting strings")
            encrypter = EncryptStrings()
            tree = encrypter.visit(tree)
            if self.config.verbose:
                if hasattr(encrypter, 'count'):
                    logger.info(f"Successfully encrypted {encrypter.count} strings")
                logger.success("Encrypted string literals")
        
        # Apply function body wrapping if specified
        if self.config.dynamic_exec:
            if self.config.verbose:
                logger.info("Wrapping function bodies with dynamic exec")
            wrapper = DynamicFunctionBody()
            tree = wrapper.visit(tree)
            if self.config.verbose:
                if hasattr(wrapper, 'count'):
                    logger.info(f"Successfully wrapped {wrapper.count} function bodies")
                logger.success("Wrapped function bodies")
        
        # Fix missing locations
        logger.info("Fixing missing locations in AST") if self.config.verbose else None
        ast.fix_missing_locations(tree)

        # Unparse AST to source code
        logger.info("Unparsing AST to source code") if self.config.verbose else None
        obfuscated_code = astunparse.unparse(tree)
        if self.config.verbose:
            logger.info(f"Generated {len(obfuscated_code)} bytes of obfuscated code")

        # Fix slice syntax issues
        logger.info("Fixing slice syntax issues") if self.config.verbose else None
        obfuscated_code = fix_slice_syntax(obfuscated_code)

        # Apply encryption layers if requested
        if self.config.encrypt > 0:
            if self.config.verbose:
                logger.info(f"Applying {self.config.encrypt} encryption layers")
            for i in range(self.config.encrypt):
                method = random.randint(1, 4)
                if self.config.verbose:
                    logger.info(f"Applying encryption method {method} (layer {i+1}/{self.config.encrypt})")
                if method == 1:
                    obfuscated_code = encryption_method_1(obfuscated_code)
                elif method == 2:
                    obfuscated_code = encryption_method_2(obfuscated_code)
                elif method == 3:
                    obfuscated_code = encryption_method_3(obfuscated_code)
                else:
                    obfuscated_code = encryption_method_4(obfuscated_code)
                if self.config.verbose:
                    logger.info(f"Layer {i+1} encryption complete, code size: {len(obfuscated_code)} bytes")
            
            if self.config.verbose:
                logger.success(f"Applied {self.config.encrypt} encryption layers")

        # Write output file
        logger.info(f"Writing obfuscated code to {self.config.output_file}")
        with open(self.config.output_file, "w", encoding="utf-8") as f:
            f.write(obfuscated_code)
            
        # Always show completion message
        logger.success(f"Obfuscation completed successfully")
            
def obfuscate_file(input_file: str, output_file: str, **kwargs) -> None:
    """
    Obfuscate a Python file with the specified options.
    
    Args:
        input_file: Path to the input Python file
        output_file: Path to write the obfuscated output
        **kwargs: Additional configuration options
    """
    # Create config from arguments
    config = ObfuscationConfig(
        input_file=input_file,
        output_file=output_file,
        **kwargs
    )
    
    # Make sure remove_comments is recognized as a valid technique
    # even though it's now the default behavior
    explicitly_selected = (
        config.encrypt > 0 or 
        config.junk_code > 0 or 
        config.obfuscate_imports or 
        config.identifier_rename or 
        config.dynamic_exec or 
        config.encrypt_strings
    )
    
    # If nothing else is selected, make sure we still consider
    # comment removal as a valid option to avoid the error
    # (even though it would be applied anyway)
    if not explicitly_selected and not config.all_techniques:
        # At this point we're only using remove_comments (which is default)
        if config.verbose:
            logger.info("Only applying comment removal (default behavior)")
    
    # Create obfuscator and run
    obfuscator = Obfuscator(config)
    obfuscator.obfuscate() 