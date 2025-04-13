from typing import Dict, Any, List, Optional
import time
import re
import random

from pyfuscator.config import ObfuscationConfig
from pyfuscator.log_utils import logger
from pyfuscator.transformers.powershell.identifiers import RenameIdentifiers
from pyfuscator.transformers.powershell.strings import ObfuscateStrings
from pyfuscator.transformers.powershell.concat import CommandTokenizer
from pyfuscator.transformers.powershell.junk import InsertJunkCode
from pyfuscator.transformers.powershell.dotnet import UseDotNetMethods
from pyfuscator.transformers.powershell.securestring import SecureStringTransformer
from pyfuscator.transformers.powershell.ads import AlternateDataStreams
from pyfuscator.transformers.powershell.remove_comments import RemoveComments
from pyfuscator.transformers.powershell.lower_entropy import LowerEntropy
from pyfuscator.transformers.powershell.base64 import Base64Encoder
from pyfuscator.transformers.powershell.script_encryptor import PowerShellScriptEncryptor

class PowerShellObfuscator:
    """Main class for PowerShell obfuscation."""

    def __init__(self, config=None):
        """Initialize the PowerShell obfuscator.

        Args:
            config (dict, optional): Configuration options for the obfuscator.
        """
        self.config = config or {}
        self.logger = logger
        self.original_code = None
        self.obfuscated_code = None
        self.stats = {}
        
        # Initialize transformers to None
        self.identifier_renamer = None
        self.string_obfuscator = None
        self.command_tokenizer = None
        self.junk_code_inserter = None
        self.dotnet_methods = None
        self.secure_string = None
        self.ads_utility = None
        self.comment_remover = None
        self.entropy_reducer = None
        self.base64_encoder = None
        self.script_encryptor = None
        self.string_divider = None
        
        # Initialize ADS utility if needed
        if hasattr(self.config, 'use_ads') and self.config.use_ads:
            self.ads_utility = AlternateDataStreams()

    def obfuscate(self, input_code):
        """Obfuscate PowerShell code.

        Args:
            input_code (str): Original PowerShell code

        Returns:
            str: Obfuscated PowerShell code
        """
        self.original_code = input_code
        self.obfuscated_code = input_code
        obfuscation_applied = False
        is_verbose = self.config.get('verbose', False)
        
        # Track start time for performance logging
        start_time = time.time()
        
        # Check if base64-full is directly requested without other base64 options
        if self.config.get('base64_full', False) and not self.config.get('base64_commands', False):
            if is_verbose:
                self.logger.info("Full Base64 encoding of entire script requested")
            
            # Apply comment removal first if enabled
            if self.config.get('remove_comments', True):
                if is_verbose:
                    self.logger.info("Removing comments before full Base64 encoding")
                self.comment_remover = RemoveComments()
                self.obfuscated_code = self.comment_remover.transform(self.obfuscated_code)
                self._update_stats(self.comment_remover.get_stats())
            
            # Apply full Base64 encoding directly
            if is_verbose:
                self.logger.info("Encoding entire script with Base64")
            
            self.base64_encoder = Base64Encoder(encode_blocks=False, encode_full=True, encode_individual=False)
            self.obfuscated_code = self.base64_encoder._encode_full_script(self.obfuscated_code)
            self.stats["encoded_full_script"] = True
            
            if is_verbose:
                self.logger.success("Encoded entire script with Base64")
            
            # Record processing time
            processing_time = time.time() - start_time
            self.stats['processing_time'] = processing_time
            
            if is_verbose:
                self.logger.info(f"Total obfuscation processing time: {processing_time:.2f} seconds")
            
            return self.obfuscated_code
            
        # Check if we're using --all option for ordered application of techniques
        if (
            self.config.get('rename_identifiers', False) and 
            self.config.get('junk_code', 0) == 200 and
            self.config.get('tokenize_commands', False) and
            self.config.get('string_divide', False) and
            self.config.get('base64_encode', False) and
            self.config.get('lower_entropy', False) and
            not self.config.get('base64_full', False) and
            not self.config.get('base64_commands', False)
        ):
            # Using --all option, apply techniques in the required order
            if is_verbose:
                self.logger.info("Using --all option with specified technique order")
            return self._obfuscate_ordered(input_code, is_verbose)
        
        # Initial code analysis
        if is_verbose:
            self.logger.info("Analyzing PowerShell script structure")
            self.logger.info(f"Script size: {len(self.obfuscated_code)} bytes")
            # Count approximate number of functions, variables, etc.
            func_count = len(re.findall(r'(?i)function\s+([a-zA-Z0-9_-]+)', self.obfuscated_code))
            var_count = len(re.findall(r'\$([a-zA-Z0-9_]+)\s*=', self.obfuscated_code))
            self.logger.info(f"Found approximately {func_count} functions and {var_count} variables")
        
        # 1. Remove comments if requested (enabled by default)
        if self.config.get('remove_comments', True):
            if is_verbose:
                self.logger.info("Removing comments from PowerShell code")
                self.logger.info("Looking for single-line (#) and multi-line (<# #>) comments to remove")
                original_length = len(self.obfuscated_code)
            
            self.comment_remover = RemoveComments()
            self.obfuscated_code = self.comment_remover.transform(self.obfuscated_code)
            self._update_stats(self.comment_remover.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                new_length = len(self.obfuscated_code)
                reduction = original_length - new_length
                percentage = (reduction / original_length) * 100 if original_length > 0 else 0
                self.logger.success(f"Removed {self.stats.get('removed_comment_count', 0)} comments, "
                                f"{self.stats.get('removed_comment_chars', 0)} characters ({percentage:.1f}% size reduction)")
        
        # Apply string division if requested
        if self.config.get('string_divide', False):
            if is_verbose:
                self.logger.info("Dividing strings in PowerShell code")
                self.logger.info("Breaking strings into concatenated parts for obfuscation")
            
            # Configure the string obfuscator specifically for string division
            self.string_divider = ObfuscateStrings(
                split_min=2,  # At least split into 2 parts
                split_max=4,  # Split into at most 4 parts
                obfuscation_probability=1.0  # Apply to all strings
            )
            self.obfuscated_code = self.string_divider.transform(self.obfuscated_code)
            self._update_stats(self.string_divider.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success(f"Divided {self.stats.get('strings_obfuscated', 0)} strings into concatenated parts")
        
        # 2. Apply Lower Entropy transformation early if requested
        if self.config.get('lower_entropy', False):
            if is_verbose:
                self.logger.info("Applying lower entropy transformation")
                self.logger.info("Adding random whitespace, substituting aliases, and reordering code blocks")
                
            self.entropy_reducer = LowerEntropy()
            self.obfuscated_code = self.entropy_reducer.transform(self.obfuscated_code)
            self._update_stats(self.entropy_reducer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success(f"Applied entropy reduction: added {self.stats.get('spaces_inserted', 0)} random spaces, "
                                f"substituted {self.stats.get('aliases_substituted', 0)} aliases, "
                                f"reordered {self.stats.get('blocks_reordered', 0)} code blocks")
        
        # 3. Apply rename identifiers if requested
        if self.config.get('rename_identifiers', False):
            if is_verbose:
                self.logger.info("Preparing to obfuscate PowerShell identifiers")
                self.logger.info("Scanning script for variables, functions, and parameters")
                
            self.identifier_renamer = RenameIdentifiers()
            
            if is_verbose:
                pre_rename_size = len(self.obfuscated_code)
                # Count functions and variables
                func_pattern = r'(?i)function\s+([a-zA-Z0-9_-]+)'
                var_pattern = r'\$([a-zA-Z0-9_]+)\s*='
                func_matches = len(re.findall(func_pattern, self.obfuscated_code))
                var_matches = len(re.findall(var_pattern, self.obfuscated_code))
                self.logger.info(f"Found {func_matches} functions and {var_matches} variables to potentially rename")
                self.logger.info("Generating random identifiers for renaming")
            
            self.obfuscated_code = self.identifier_renamer.transform(self.obfuscated_code)
            self._update_stats(self.identifier_renamer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                post_rename_size = len(self.obfuscated_code)
                func_renamed = self.stats.get('functions_renamed', 0)
                var_renamed = self.stats.get('variables_renamed', 0)
                self.logger.success(f"Successfully renamed {func_renamed} functions and {var_renamed} variables")
                self.logger.info(f"Script size after identifier renaming: {post_rename_size} bytes")
        
        # 4. Apply string obfuscation if requested
        if self.config.get('obfuscate_strings', False):
            if is_verbose:
                self.logger.info("Obfuscating PowerShell strings")
                self.logger.info("Using techniques like string splitting, format operators, character arrays, and hex encoding")
                
            self.string_obfuscator = ObfuscateStrings()
            self.obfuscated_code = self.string_obfuscator.transform(self.obfuscated_code)
            self._update_stats(self.string_obfuscator.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success(f"Obfuscated {self.stats.get('strings_obfuscated', 0)} string literals")
        
        # 5. Apply dot net method obfuscation if requested
        if self.config.get('dotnet_methods', False):
            if is_verbose:
                self.logger.info("Applying .NET method obfuscation")
                self.logger.info("Converting standard PowerShell commands to .NET method equivalents")
                
            self.dotnet_methods = UseDotNetMethods()
            self.obfuscated_code = self.dotnet_methods.transform(self.obfuscated_code)
            self._update_stats(self.dotnet_methods.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success(f"Converted {self.stats.get('dotnet_methods_applied', 0)} commands to .NET equivalents")
        
        # 6. Apply secure string obfuscation if requested
        if self.config.get('secure_strings', False):
            if is_verbose:
                self.logger.info("Applying SecureString obfuscation")
                self.logger.info("Converting string literals to SecureString objects for added protection")
                
            self.secure_string = SecureStringTransformer()
            self.obfuscated_code = self.secure_string.transform(self.obfuscated_code)
            self._update_stats(self.secure_string.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success(f"Obfuscated {self.stats.get('securestrings_applied', 0)} strings using SecureString")
        
        # 7. Apply junk code if requested
        if self.config.get('junk_code', 0) > 0:
            junk_count = self.config.get('junk_code', 0)
            if is_verbose:
                self.logger.info(f"Inserting {junk_count} junk code statements")
                self.logger.info("Generating random PowerShell statements for code obfuscation")
                pre_junk_size = len(self.obfuscated_code)
                
            self.junk_code_inserter = InsertJunkCode(junk_count)
            self.obfuscated_code = self.junk_code_inserter.transform(self.obfuscated_code)
            self._update_stats(self.junk_code_inserter.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                post_junk_size = len(self.obfuscated_code)
                size_increase = post_junk_size - pre_junk_size
                percentage = (size_increase / pre_junk_size) * 100 if pre_junk_size > 0 else 0
                actual_junk = self.stats.get('junk_statements_added', junk_count)
                self.logger.success(f"Added {actual_junk} junk statements, increasing script size by {size_increase} bytes ({percentage:.1f}%)")
        
        # 8. Apply command tokenization if requested
        if self.config.get('tokenize_commands', False):
            if is_verbose:
                self.logger.info("Tokenizing PowerShell commands")
                self.logger.info("Breaking commands into parts to evade signature-based detection")
                
            self.command_tokenizer = CommandTokenizer()
            self.obfuscated_code = self.command_tokenizer.transform(self.obfuscated_code)
            self._update_stats(self.command_tokenizer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                tokenized = self.stats.get('commands_tokenized', 0)
                self.logger.success(f"Tokenized {tokenized} PowerShell commands")
        
        # 9. Apply Base64 encoding to individual commands if requested
        if self.config.get('base64_commands', False):
            if is_verbose:
                self.logger.info("Encoding individual commands with Base64")
                self.logger.info("This helps bypass content filtering and signature detection")
                
            self.base64_encoder = Base64Encoder(encode_blocks=True, encode_full=False, encode_individual=True)
            self.obfuscated_code = self.base64_encoder.transform(self.obfuscated_code)
            self._update_stats(self.base64_encoder.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                encoded = self.stats.get('commands_encoded', 0)
                self.logger.success(f"Base64 encoded {encoded} individual commands")
        
        # 10. Apply script encryption if requested
        if self.config.get('script_encrypt', False):
            if is_verbose:
                self.logger.info("Applying script encryption")
                self.logger.info("Encrypting the entire script with secure methods")
                
            self.script_encryptor = PowerShellScriptEncryptor()
            self.obfuscated_code = self.script_encryptor.transform(self.obfuscated_code)
            self._update_stats(self.script_encryptor.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.success("Successfully encrypted the entire script")
                enc_type = self.stats.get('encryption_type', 'standard')
                self.logger.info(f"Encryption type: {enc_type}")
        
        # 11. Apply full Base64 encoding if requested
        if self.config.get('base64_full', False):
            if is_verbose:
                self.logger.info("Encoding entire script with Base64")
                self.logger.info("This provides a layer of obfuscation for the entire script")
                
            self.base64_encoder = Base64Encoder(encode_blocks=False, encode_full=True, encode_individual=False)
            self.obfuscated_code = self.base64_encoder._encode_full_script(self.obfuscated_code)
            self.stats["encoded_full_script"] = True
            
            if is_verbose:
                self.logger.success("Successfully Base64 encoded the entire script")
        
        # 12. Apply ADS storage if requested (Windows only)
        if self.config.get('use_ads', False):
            if is_verbose:
                self.logger.info("Preparing Alternate Data Stream storage (Windows only)")
                self.logger.info("This technique uses NTFS file streams to hide script content")
                
            if not self.ads_utility:
                self.ads_utility = AlternateDataStreams()
            
            ads_code = self.ads_utility.prepare_ads_script(self.obfuscated_code)
            # Only replace code if ads preparation was successful
            if ads_code:
                self.obfuscated_code = ads_code
                self.stats["used_ads"] = True
                
                if is_verbose:
                    self.logger.success("Prepared script for Alternate Data Stream storage")
            else:
                if is_verbose:
                    self.logger.warning("ADS preparation failed - this feature requires Windows")
        
        # If nothing was applied, the original code is returned
        if not obfuscation_applied:
            self.logger.warning("No obfuscation techniques were applied")
            
        # Record final processing time
        processing_time = time.time() - start_time
        self.stats['processing_time'] = processing_time
        
        if is_verbose:
            final_size = len(self.obfuscated_code)
            original_size = len(self.original_code)
            size_diff = final_size - original_size
            percent = (size_diff / original_size) * 100 if original_size > 0 else 0
            self.logger.info(f"Final script size: {final_size} bytes ({size_diff:+} bytes, {percent:.1f}% change)")
            self.logger.info(f"Total obfuscation processing time: {processing_time:.2f} seconds")
        
        return self.obfuscated_code

    def _update_stats(self, stats):
        self.stats.update(stats)

    def obfuscate_with_ads(self, content: str) -> str:
        """
        Apply obfuscation transformers to PowerShell script content.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Obfuscated PowerShell script
        """
        if not content.strip():
            logger.warning("Empty PowerShell script, nothing to obfuscate")
            return content
            
        transformed = content
        is_verbose = self.config.verbose if hasattr(self.config, 'verbose') else False
        
        # Apply comment removal first if specified
        if self.config.remove_comments:
            logger.info("Removing comments from PowerShell script")
            if is_verbose:
                logger.info("Looking for single-line (#) and multi-line (<# #>) comments to remove")
                original_length = len(transformed)
                
            comments_remover = RemoveComments()
            transformed = comments_remover.transform(transformed)
            
            if is_verbose:
                new_length = len(transformed)
                reduction = original_length - new_length
                percentage = (reduction / original_length) * 100 if original_length > 0 else 0
                logger.info(f"Removed {comments_remover.stats.get('removed_comment_count', 0)} comments, "
                            f"{comments_remover.stats.get('removed_comment_chars', 0)} characters ({percentage:.1f}% size reduction)")
                logger.success("Removed comments from PowerShell script")
        
        # Apply Lower Entropy transformation early if specified
        if hasattr(self.config, 'lower_entropy') and self.config.lower_entropy:
            logger.info("Applying lower entropy transformation to PowerShell script")
            if is_verbose:
                logger.info("Adding random whitespace, substituting aliases, and reordering code blocks")
                
            entropy_reducer = LowerEntropy()
            transformed = entropy_reducer.transform(transformed)
            
            if is_verbose:
                logger.info(f"Added {entropy_reducer.stats.get('spaces_inserted', 0)} random spaces, "
                            f"substituted {entropy_reducer.stats.get('aliases_substituted', 0)} PowerShell aliases, "
                            f"reordered {entropy_reducer.stats.get('blocks_reordered', 0)} code blocks")
                logger.success("Applied lower entropy transformation to PowerShell script")
        
        # Apply identifier renaming if specified
        if self.config.identifier_rename:
            logger.info("Renaming identifiers in PowerShell script")
            if is_verbose:
                logger.info("Renaming variables, functions, and parameters with random names")
                
            renamer = RenameIdentifiers()
            transformed = renamer.transform(transformed)
            
            if is_verbose:
                logger.info(f"Renamed {renamer.stats.get('variables_renamed', 0)} variables, "
                            f"{renamer.stats.get('functions_renamed', 0)} functions, "
                            f"and {renamer.stats.get('parameters_renamed', 0)} parameters")
                logger.success("Renamed identifiers in PowerShell script")
        
        # Apply string obfuscation if specified
        if self.config.encrypt_strings:
            logger.info("Obfuscating strings in PowerShell script")
            if is_verbose:
                logger.info("Using techniques like string splitting, format operators, character arrays, and hex encoding")
                
            string_obfuscator = ObfuscateStrings()
            transformed = string_obfuscator.transform(transformed)
            
            if is_verbose:
                logger.info(f"Obfuscated {string_obfuscator.stats.get('strings_obfuscated', 0)} string literals with mixed techniques")
                logger.success("Obfuscated strings in PowerShell script")
        
        # Apply SecureString obfuscation
        # This is a PowerShell-specific technique with no direct Python equivalent
        if self.config.encrypt_strings:
            logger.info("Applying SecureString obfuscation to PowerShell script")
            if is_verbose:
                logger.info("Using PowerShell SecureString to protect string values")
                
            secure_obfuscator = SecureStringTransformer()
            transformed = secure_obfuscator.transform(transformed)
            
            if is_verbose:
                logger.info(f"Protected {secure_obfuscator.stats.get('secure_strings_count', 0)} strings with SecureString")
                logger.success("Applied SecureString obfuscation to PowerShell script")
                
        # Apply .NET method-based obfuscation
        # This corresponds to dynamic execution in Python scripts
        if self.config.dynamic_exec:
            logger.info("Applying .NET method obfuscation to PowerShell script")
            if is_verbose:
                logger.info("Replacing standard PowerShell operations with .NET method equivalents")
                
            dotnet_transformer = UseDotNetMethods()
            transformed = dotnet_transformer.transform(transformed)
            
            if is_verbose:
                logger.info(f"Replaced {dotnet_transformer.stats.get('dotnet_substitutions', 0)} operations with .NET methods")
                logger.success("Applied .NET method obfuscation to PowerShell script")
        
        # Apply command tokenization
        # This corresponds to import obfuscation in Python scripts
        if self.config.obfuscate_imports:
            logger.info("Tokenizing commands in PowerShell script")
            if is_verbose:
                logger.info("Breaking commands into tokens and reconstructing them at runtime")
                
            tokenizer = CommandTokenizer()
            transformed = tokenizer.transform(transformed)
            
            if is_verbose:
                logger.info(f"Tokenized {tokenizer.stats.get('tokenized_commands', 0)} commands and "
                            f"{tokenizer.stats.get('tokenized_functions', 0)} functions")
                logger.success("Tokenized commands in PowerShell script")
        
        # Apply junk code insertion if specified
        if self.config.junk_code > 0:
            logger.info(f"Inserting {self.config.junk_code} junk statements into PowerShell script")
            if is_verbose:
                logger.info("Inserting meaningless code blocks to confuse analysis")
                
            junk_inserter = InsertJunkCode(num_statements=self.config.junk_code)
            transformed = junk_inserter.transform(transformed)
            
            if is_verbose:
                junk_added = junk_inserter.stats.get('junk_statements_added', 0)
                junk_percentage = (junk_added / self.config.junk_code) * 100
                logger.info(f"Added {junk_added} junk statements ({junk_percentage:.1f}% of requested)")
                logger.success(f"Inserted junk code into PowerShell script")
        
        # Apply Base64 encoding if specified
        if self.config.base64_encode:
            logger.info("Applying Base64 encoding to PowerShell script")
            # Fix: Correctly use the configuration parameters with proper defaults
            encode_blocks = True  # Default behavior for base64_encode
            encode_full = self.config.get('base64_full', False)
            encode_cmds = self.config.get('base64_commands', False)
            
            if is_verbose:
                encoding_types = []
                if encode_blocks:
                    encoding_types.append("script blocks")
                if encode_full:
                    encoding_types.append("full script")
                if encode_cmds:
                    encoding_types.append("individual commands")
                logger.info(f"Encoding {', '.join(encoding_types)} with Base64")
                
            base64_encoder = Base64Encoder(
                encode_blocks=encode_blocks,
                encode_full=encode_full,
                encode_individual=encode_cmds
            )
            
            # Apply the transformation
            prev_code = transformed
            transformed = base64_encoder.transform(transformed)
            # Verify transformation happened and force it if needed
            if prev_code == transformed and encode_full:
                if is_verbose:
                    logger.info("Forcing full script Base64 encoding")
                transformed = base64_encoder._encode_full_script(prev_code)
                base64_encoder.stats["encoded_full_script"] = True
            
            if is_verbose:
                if base64_encoder.stats.get('encoded_full_script', False):
                    logger.info("Encoded entire script with Base64")
                else:
                    logger.info(f"Encoded {base64_encoder.stats.get('blocks_encoded', 0)} script blocks and "
                               f"{base64_encoder.stats.get('commands_encoded', 0)} commands with Base64")
                logger.success("Applied Base64 encoding to PowerShell script")
        
        # Apply ADS storage if configured (after all other transformations)
        if self.ads_utility and hasattr(self.config, 'use_ads') and self.config.use_ads:
            logger.info("Preparing script for Alternate Data Streams storage")
            if is_verbose:
                logger.info("Creating NTFS Alternate Data Stream to hide the script content")
                
            # The return here is a loader script that will extract from ADS
            try:
                # Create temporary output with transformed content
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ps1') as temp_file:
                    temp_file.write(transformed.encode('utf-8'))
                    temp_path = temp_file.name
                
                # Use ADS utility to create a base file and store script in ADS
                base_file, loader_script = self.ads_utility.store_in_ads(temp_path)
                
                # Return the loader script
                transformed = loader_script
                
                if is_verbose:
                    logger.info(f"Script content hidden in alternate data stream of {base_file}")
                logger.success("Script prepared for Alternate Data Streams storage")
            except Exception as e:
                logger.error(f"Failed to prepare for ADS storage: {str(e)}")
                logger.warning("Continuing with standard obfuscation")
                
        # Apply script encryption if specified - always apply last
        if self.config.script_encrypt:
            logger.info("Encrypting PowerShell script")
            if is_verbose:
                logger.info("Using SecureString to encrypt the entire script with a random key")
                
            script_encryptor = PowerShellScriptEncryptor(
                generate_launcher=self.config.get('generate_launcher', True)
            )
            transformed = script_encryptor.transform(transformed)
            
            if is_verbose:
                key_length = script_encryptor.stats.get("encryption_key_length", 0)
                logger.info(f"Encrypted script with a {key_length * 8}-bit key and generated a launcher")
                logger.success("Encrypted PowerShell script")
        
        if is_verbose:
            original_size = len(content)
            final_size = len(transformed)
            growth = ((final_size - original_size) / original_size) * 100
            logger.info(f"Obfuscation complete. Script size changed from {original_size:,} to {final_size:,} bytes ({growth:+.1f}%)")
            
        return transformed

    def _tokenize_command(self, command: str) -> str:
        """Obfuscate PowerShell commands using token splitting."""
        # Split the command into parts
        parts = re.split(r'(\W+)', command)
        
        # New: Handle command arguments properly
        if ' ' in command:
            cmd, args = command.split(' ', 1)
            obfuscated_cmd = self._obfuscate_command_name(cmd)
            return f"{obfuscated_cmd} {args}"  # Preserve arguments after space
        else:
            return self._obfuscate_command_name(command)

    def _obfuscate_command_name(self, cmd: str) -> str:
        """Obfuscate individual command names with multiple methods."""
        # Randomly select obfuscation method
        method = random.choice([
            self._string_concat_method,
            self._char_array_method,
            self._script_block_method
        ])
        return method(cmd)

    def _char_array_method(self, cmd: str) -> str:
        """Obfuscate using char array with proper invocation."""
        chars = [f"'{c}'" for c in cmd]
        return f"&([char[]]({','.join(chars)})-join'')"

    def _script_block_method(self, cmd: str) -> str:
        """Obfuscate using script blocks with proper invocation."""
        parts = []
        for i, c in enumerate(cmd):
            var_name = f"$p{i}_{random_name(4)}"
            parts.append(f"{var_name}='{c}'")
        parts_str = ';'.join(parts)
        return f"& ({{{parts_str};(& (${{0}}))}} -f ({'+'.join([p.split('=')[0] for p in parts])}))"

    def _obfuscate_ordered(self, input_code, is_verbose):
        """Apply obfuscation techniques in the specific order required by the -a option.
        
        The defined order is:
        1. Comment removal (-r)
        2. Identifier renaming (-i)
        3. Junk code insertion (-j 200)
        4. Lower entropy (-l)
        5. Tokenization (-c)
        6. String division (-sd)
        7. Base64 encode (-b) - individual command encoding, not full script
        
        Args:
            input_code: Original PowerShell code
            is_verbose: Whether to show verbose logging
            
        Returns:
            Obfuscated PowerShell code
        """
        if is_verbose:
            self.logger.info("Applying standard obfuscation sequence in exact order:")
            self.logger.info("1. Comment removal → 2. Identifier renaming → 3. Junk code insertion → "
                           "4. Lower entropy → 5. Command tokenization → 6. String division → "
                           "7. Base64 encoding")
            self.logger.info(f"Initial script size: {len(input_code)} bytes")
            func_count = len(re.findall(r'(?i)function\s+([a-zA-Z0-9_-]+)', input_code))
            var_count = len(re.findall(r'\$([a-zA-Z0-9_]+)\s*=', input_code))
            self.logger.info(f"Found approximately {func_count} functions and {var_count} variables in original script")
        
        # Process the code using the specified obfuscation order
        processed_code = input_code
        
        # 1. Comment removal
        if is_verbose:
            self.logger.info("STEP 1/7: Removing comments from PowerShell code")
            self.logger.info("Looking for single-line (#) and multi-line (<# #>) comments to remove")
            original_length = len(processed_code)
            
        comment_remover = RemoveComments()
        processed_code = comment_remover.transform(processed_code)
        self._update_stats(comment_remover.get_stats())
        
        if is_verbose:
            new_length = len(processed_code)
            reduction = original_length - new_length
            percentage = (reduction / original_length) * 100 if original_length > 0 else 0
            self.logger.success(f"STEP 1/7 COMPLETE: Removed {self.stats.get('removed_comment_count', 0)} comments, {reduction} bytes ({percentage:.1f}% reduction)")
        
        # 2. Identifier renaming
        if is_verbose:
            self.logger.info("STEP 2/7: Renaming variables and functions")
            self.logger.info("Scanning script for variables, functions, and parameters to rename")
            pre_rename_size = len(processed_code)
            func_pattern = r'(?i)function\s+([a-zA-Z0-9_-]+)'
            var_pattern = r'\$([a-zA-Z0-9_]+)\s*='
            func_matches = len(re.findall(func_pattern, processed_code))
            var_matches = len(re.findall(var_pattern, processed_code))
            self.logger.info(f"Found {func_matches} functions and {var_matches} variables to potentially rename")
            
        self.identifier_renamer = RenameIdentifiers()
        processed_code = self.identifier_renamer.transform(processed_code)
        self._update_stats(self.identifier_renamer.get_stats())
        
        if is_verbose:
            post_rename_size = len(processed_code)
            size_diff = post_rename_size - pre_rename_size
            func_renamed = self.stats.get('functions_renamed', 0)
            var_renamed = self.stats.get('variables_renamed', 0)
            self.logger.success(f"STEP 2/7 COMPLETE: Renamed {func_renamed} functions and {var_renamed} variables")
            self.logger.info(f"Script size after renaming: {post_rename_size} bytes ({size_diff:+} bytes)")
        
        # 3. Junk code insertion
        if is_verbose:
            self.logger.info("STEP 3/7: Inserting junk code statements (200)")
            self.logger.info("Generating 200 random PowerShell statements to add obfuscation")
            pre_junk_size = len(processed_code)
            
        junk_code_inserter = InsertJunkCode(200)
        processed_code = junk_code_inserter.transform(processed_code)
        self._update_stats(junk_code_inserter.get_stats())
        
        if is_verbose:
            post_junk_size = len(processed_code)
            size_increase = post_junk_size - pre_junk_size
            percentage = (size_increase / pre_junk_size) * 100 if pre_junk_size > 0 else 0
            actual_junk = self.stats.get('junk_statements_added', 200)
            self.logger.success(f"STEP 3/7 COMPLETE: Added {actual_junk} junk statements")
            self.logger.info(f"Script size after junk insertion: {post_junk_size} bytes (+{size_increase} bytes, {percentage:.1f}% increase)")
        
        # 4. Lower entropy transformation
        if is_verbose:
            self.logger.info("STEP 4/7: Applying lower entropy transformation")
            self.logger.info("Adding random whitespace, substituting aliases, and reordering code blocks")
            pre_entropy_size = len(processed_code)
            
        entropy_reducer = LowerEntropy()
        processed_code = entropy_reducer.transform(processed_code)
        self._update_stats(entropy_reducer.get_stats())
        
        if is_verbose:
            post_entropy_size = len(processed_code)
            size_diff = post_entropy_size - pre_entropy_size
            spaces = self.stats.get('spaces_inserted', 0)
            aliases = self.stats.get('aliases_substituted', 0)
            blocks = self.stats.get('blocks_reordered', 0)
            self.logger.success(f"STEP 4/7 COMPLETE: Added {spaces} random spaces, substituted {aliases} aliases, reordered {blocks} code blocks")
            self.logger.info(f"Script size after entropy reduction: {post_entropy_size} bytes ({size_diff:+} bytes)")
        
        # 5. Command tokenization
        if is_verbose:
            self.logger.info("STEP 5/7: Tokenizing PowerShell commands")
            self.logger.info("Breaking commands into parts to evade signature-based detection")
            pre_token_size = len(processed_code)
            
        command_tokenizer = CommandTokenizer()
        processed_code = command_tokenizer.transform(processed_code)
        # Update stats with the correct key name - commands_tokenized instead of tokenized_commands
        tokenizer_stats = command_tokenizer.get_stats()
        self.stats["commands_tokenized"] = tokenizer_stats.get("tokenized_commands", 0)
        self.stats["functions_tokenized"] = tokenizer_stats.get("tokenized_functions", 0)
        
        if is_verbose:
            post_token_size = len(processed_code)
            size_diff = post_token_size - pre_token_size
            tokenized = self.stats.get('commands_tokenized', 0) + self.stats.get('functions_tokenized', 0)
            self.logger.success(f"STEP 5/7 COMPLETE: Tokenized {tokenized} PowerShell commands/functions")
            self.logger.info(f"Script size after tokenization: {post_token_size} bytes ({size_diff:+} bytes)")
        
        # 6. String division
        if is_verbose:
            self.logger.info("STEP 6/7: Dividing strings into concatenated parts")
            self.logger.info("Breaking string literals into smaller pieces to avoid detection")
            pre_divide_size = len(processed_code)
            
        string_divider = ObfuscateStrings(
            split_min=2,
            split_max=4,
            obfuscation_probability=1.0
        )
        processed_code = string_divider.transform(processed_code)
        self._update_stats(string_divider.get_stats())
        
        if is_verbose:
            post_divide_size = len(processed_code)
            size_diff = post_divide_size - pre_divide_size
            divided = self.stats.get('strings_obfuscated', 0)
            self.logger.success(f"STEP 6/7 COMPLETE: Divided {divided} strings into concatenated parts")
            self.logger.info(f"Script size after string division: {post_divide_size} bytes ({size_diff:+} bytes)")
        
        # 7. Base64 encoding (only individual commands, not full script)
        if is_verbose:
            self.logger.info("STEP 7/7: Encoding individual commands with Base64")
            self.logger.info("Using Base64 encoding to bypass content filtering")
            pre_base64_size = len(processed_code)
            
        # Use encode_individual=True to encode individual commands rather than blocks or full script
        base64_encoder = Base64Encoder(
            encode_blocks=False,
            encode_full=False,
            encode_individual=True
        )
        processed_code = base64_encoder.transform(processed_code)
        self._update_stats(base64_encoder.get_stats())
        
        if is_verbose:
            post_base64_size = len(processed_code)
            size_diff = post_base64_size - pre_base64_size
            encoded = self.stats.get('commands_encoded', 0)
            self.logger.success(f"STEP 7/7 COMPLETE: Base64 encoded {encoded} individual commands")
            self.logger.info(f"Script size after Base64 encoding: {post_base64_size} bytes ({size_diff:+} bytes)")
            
            # Final summary
            final_size = len(processed_code)
            original_size = len(input_code)
            total_diff = final_size - original_size
            total_percent = (total_diff / original_size) * 100 if original_size > 0 else 0
            self.logger.info(f"All steps complete. Final script size: {final_size} bytes (+{total_diff} bytes, {total_percent:.1f}% increase from original)")
        
        return processed_code