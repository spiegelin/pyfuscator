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
            self.stats['obfuscated_imports'] = len(IMPORT_MAPPING)
            
            # Success message
            self.logger.success(f"Obfuscated import statements")
            
        # Apply identifier renaming if specified
        if self.config.get('rename_identifiers', False):
            # Only use import-aware mode if import obfuscation is also enabled
            import_aware = self.config.get('obfuscate_imports', False)
            if self.config.get('verbose', False):
                self.logger.info("Renaming identifiers" + (" (with import tracking)" if not import_aware else ""))
            
            rename_identifiers = RenameIdentifiers(import_aware=import_aware)
            tree = rename_identifiers.visit(tree)
            
            # Only rename imports separately if we're not already obfuscating imports
            if not self.config.get('obfuscate_imports', False):
                if self.config.get('verbose', False):
                    self.logger.info("Renaming import statements")
                tree = ImportRenamer(rename_identifiers.import_mapping).visit(tree)
            
            # Update stats
            self.stats['renamed_identifiers'] = len(rename_identifiers.mapping)
                
            # Success message
            self.logger.success(f"Renamed identifiers")
        
        # Apply string encryption if enabled
        if self.config.get('encrypt_strings', False):
            if self.config.get('verbose', False):
                self.logger.info("Encrypting strings")
            
            encrypter = EncryptStrings()
            tree = encrypter.visit(tree)
            
            # Update stats
            self.stats['encrypted_strings'] = getattr(encrypter, 'count', 0)
            
            # Success message
            self.logger.success("Encrypted string literals")
        
        # Apply function body wrapping if specified
        if self.config.get('dynamic_execution', False):
            if self.config.get('verbose', False):
                self.logger.info("Wrapping function bodies with dynamic exec")
            
            wrapper = DynamicFunctionBody()
            tree = wrapper.visit(tree)
            
            # Update stats
            self.stats['functions_wrapped'] = getattr(wrapper, 'count', 0)
            
            # Success message
            self.logger.success("Wrapped function bodies")
        
        # Fix missing locations
        if self.config.get('verbose', False):
            self.logger.info("Fixing missing locations in AST")
        ast.fix_missing_locations(tree)

        # Unparse AST to source code
        if self.config.get('verbose', False):
            self.logger.info("Unparsing AST to source code")
        obfuscated_code = astunparse.unparse(tree)
        if self.config.get('verbose', False):
            self.logger.info(f"Generated {len(obfuscated_code)} bytes of obfuscated code")

        # Fix slice syntax issues
        if self.config.get('verbose', False):
            self.logger.info("Fixing slice syntax issues")
        obfuscated_code = fix_slice_syntax(obfuscated_code)

        # Apply encryption layers if requested
        if self.config.get('encrypt_layers', 0) > 0:
            encrypt_layers = self.config.get('encrypt_layers', 0)
            if self.config.get('verbose', False):
                self.logger.info(f"Applying {encrypt_layers} encryption layers")
            
            for i in range(encrypt_layers):
                method = random.randint(1, 4)
                if self.config.get('verbose', False):
                    self.logger.info(f"Applying encryption method {method} (layer {i+1}/{encrypt_layers})")
                
                if method == 1:
                    obfuscated_code = encryption_method_1(obfuscated_code)
                elif method == 2:
                    obfuscated_code = encryption_method_2(obfuscated_code)
                elif method == 3:
                    obfuscated_code = encryption_method_3(obfuscated_code)
                else:
                    obfuscated_code = encryption_method_4(obfuscated_code)
                
                if self.config.get('verbose', False):
                    self.logger.info(f"Layer {i+1} encryption complete, code size: {len(obfuscated_code)} bytes")
            
            # Success message
            self.logger.success(f"Applied {encrypt_layers} encryption layers")

        # Record processing time
        self.stats['processing_time'] = 0.0  # Would be set by timer in a real implementation
        
        # Always show completion message
        self.logger.success(f"Python obfuscation completed successfully")
        
        return obfuscated_code

def obfuscate_file(input_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """
    Process a file by reading its content, obfuscating it, and writing the result.
    
    Args:
        input_file: Path to the input file
        output_file: Path to the output file
        **kwargs: Configuration options for the obfuscation
    
    Returns:
        Dict containing stats about the obfuscation process
    """
    # Create configuration - remove input_file and output_file from kwargs
    config = ObfuscationConfig(**kwargs)
    
    # Store files in extra_options
    config.extra_options['input_file'] = input_file
    config.extra_options['output_file'] = output_file
    
    # Create obfuscator with the configuration
    obfuscator = Obfuscator(config)
    
    # Detect language if not specified
    if not hasattr(config, 'language') or not config.language:
        detected_language = detect_script_language(input_file)
        setattr(config, 'language', detected_language)
        
        if config.get('verbose', False):
            obfuscator.logger.info(f"Auto-detected {detected_language.capitalize()} script")
    
    # Process start time
    start_time = time.time() if config.get('verbose', False) else 0
    
    try:
        # Read the input file and check if it exists
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except FileNotFoundError:
            obfuscator.logger.error(f"Input file not found: {input_file}")
            raise
        except Exception as e:
            obfuscator.logger.error(f"Error reading {input_file}: {str(e)}")
            raise
            
        # Obfuscate the code
        result = obfuscator.obfuscate(source_code)
        
        # Get processing time
        if config.get('verbose', False):
            processing_time = time.time() - start_time
            obfuscator.stats['processing_time'] = processing_time
        
        # Write the result
        try:
            # Use UTF-8 with error handling to prevent charmap errors
            with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(result)
        except Exception as e:
            obfuscator.logger.error(f"Error writing to {output_file}: {str(e)}")
            raise
            
        return {'stats': obfuscator.stats}
        
    except Exception as e:
        # Log the error but don't raise it here
        obfuscator.logger.error(f"Obfuscation failed: {str(e)}")
        if config.get('verbose', False):
            import traceback
            obfuscator.logger.error(traceback.format_exc())
        return {'stats': {}, 'error': str(e)}

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