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
from pyfuscator.transformers.powershell.securestring import ObfuscateWithSecureString
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
        
        # 1. Remove comments if requested (enabled by default)
        if self.config.get('remove_comments', True):
            self.logger.info("Removing comments from PowerShell code...")
            if is_verbose:
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
                self.logger.info(f"Removed {self.stats.get('removed_comment_count', 0)} comments, "
                                f"{self.stats.get('removed_comment_chars', 0)} characters ({percentage:.1f}% size reduction)")
        
        # Apply string division if requested
        if self.config.get('string_divide', False):
            self.logger.info("Dividing strings in PowerShell code...")
            if is_verbose:
                self.logger.info("Breaking strings into concatenated parts")
            
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
                self.logger.info(f"Divided {self.stats.get('strings_obfuscated', 0)} strings into concatenated parts")
        
        # 2. Apply Lower Entropy transformation early if requested
        if self.config.get('lower_entropy', False):
            self.logger.info("Applying lower entropy transformation...")
            if is_verbose:
                self.logger.info("Adding random whitespace, substituting aliases, and reordering code blocks")
                
            self.entropy_reducer = LowerEntropy()
            self.obfuscated_code = self.entropy_reducer.transform(self.obfuscated_code)
            self._update_stats(self.entropy_reducer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Added {self.stats.get('spaces_inserted', 0)} random spaces, "
                                f"substituted {self.stats.get('aliases_substituted', 0)} PowerShell aliases, "
                                f"reordered {self.stats.get('blocks_reordered', 0)} code blocks")
        
        # 3. Apply rename identifiers if requested
        if self.config.get('rename_identifiers', False):
            self.logger.info("Obfuscating PowerShell identifiers...")
            if is_verbose:
                self.logger.info("Renaming variables, functions, and parameters with random names")
                
            self.identifier_renamer = RenameIdentifiers()
            self.obfuscated_code = self.identifier_renamer.transform(self.obfuscated_code)
            self._update_stats(self.identifier_renamer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Renamed {self.stats.get('variables_renamed', 0)} variables, "
                                f"{self.stats.get('functions_renamed', 0)} functions, "
                                f"and {self.stats.get('parameters_renamed', 0)} parameters")
        
        # 4. Apply string obfuscation if requested
        if self.config.get('obfuscate_strings', False):
            self.logger.info("Obfuscating PowerShell strings...")
            if is_verbose:
                self.logger.info("Using techniques like string splitting, format operators, character arrays, and hex encoding")
                
            self.string_obfuscator = ObfuscateStrings()
            self.obfuscated_code = self.string_obfuscator.transform(self.obfuscated_code)
            self._update_stats(self.string_obfuscator.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Obfuscated {self.stats.get('strings_obfuscated', 0)} string literals with mixed techniques")
        
        # 5. Apply secure string obfuscation if requested
        if self.config.get('secure_strings', False):
            self.logger.info("Applying SecureString obfuscation...")
            if is_verbose:
                self.logger.info("Using PowerShell SecureString to protect string values")
                
            self.secure_string = ObfuscateWithSecureString()
            self.obfuscated_code = self.secure_string.transform(self.obfuscated_code)
            self._update_stats(self.secure_string.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Protected {self.stats.get('secure_strings_count', 0)} strings with SecureString")
            
        # 6. Use .NET methods if requested
        if self.config.get('dotnet_methods', False):
            self.logger.info("Adding .NET method obfuscation...")
            if is_verbose:
                self.logger.info("Replacing standard PowerShell operations with .NET method equivalents")
                
            self.dotnet_methods = UseDotNetMethods()
            self.obfuscated_code = self.dotnet_methods.transform(self.obfuscated_code)
            self._update_stats(self.dotnet_methods.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Replaced {self.stats.get('dotnet_substitutions', 0)} operations with .NET methods")
            
        # 7. Tokenize commands if requested
        if self.config.get('tokenize_commands', False):
            self.logger.info("Tokenizing PowerShell commands...")
            if is_verbose:
                self.logger.info("Breaking commands into tokens and reconstructing them at runtime")
                
            self.command_tokenizer = CommandTokenizer()
            self.obfuscated_code = self.command_tokenizer.transform(self.obfuscated_code)
            self._update_stats(self.command_tokenizer.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                self.logger.info(f"Tokenized {self.stats.get('tokenized_commands', 0)} commands and "
                                f"{self.stats.get('tokenized_functions', 0)} functions")
            
        # 8. Add junk code if requested
        if junk_code_count := self.config.get('junk_code', 0):
            self.logger.info(f"Adding {junk_code_count} junk code statements...")
            if is_verbose:
                self.logger.info("Inserting meaningless code blocks to confuse analysis")
                
            self.junk_code_inserter = InsertJunkCode(junk_code_count)
            self.obfuscated_code = self.junk_code_inserter.transform(self.obfuscated_code)
            self._update_stats(self.junk_code_inserter.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                junk_added = self.stats.get('junk_statements_added', 0)
                junk_percentage = (junk_added / junk_code_count) * 100
                self.logger.info(f"Added {junk_added} junk statements ({junk_percentage:.1f}% of requested)")
            
        # 9. Apply Base64 encoding if requested - apply this closer to the end
        if self.config.get('base64_encode', False):
            self.logger.info("Applying Base64 encoding to script blocks...")
            # Fix: Properly get the configuration or use defaults
            encode_blocks = True  # Default behavior
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
                self.logger.info(f"Encoding {', '.join(encoding_types)} with Base64")
                
            # Create the Base64Encoder with correct configuration
            self.base64_encoder = Base64Encoder(
                encode_blocks=encode_blocks,
                encode_full=encode_full,
                encode_individual=encode_cmds
            )
            # Apply the transformation
            prev_code = self.obfuscated_code
            self.obfuscated_code = self.base64_encoder.transform(self.obfuscated_code)
            # Verify transformation happened
            if prev_code == self.obfuscated_code and encode_full:
                # If no change and full encoding was requested, force it
                self.obfuscated_code = self.base64_encoder._encode_full_script(prev_code)
                self.stats["encoded_full_script"] = True
            
            self._update_stats(self.base64_encoder.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                if self.stats.get('encoded_full_script', False):
                    self.logger.info("Encoded the entire script with Base64")
                else:
                    self.logger.info(f"Encoded {self.stats.get('blocks_encoded', 0)} script blocks and "
                                    f"{self.stats.get('commands_encoded', 0)} commands with Base64")
        
        # 10. Apply ADS (Alternate Data Streams) if requested (Windows only)
        if self.config.get('use_ads', False):
            self.logger.info("Adding Alternate Data Streams obfuscation...")
            if is_verbose:
                self.logger.info("Preparing to store script in NTFS Alternate Data Streams (Windows only)")
                
            self.ads_utility = AlternateDataStreams()
            # Note: ADS doesn't transform the code directly, it's used at write time
            obfuscation_applied = True
        
        # 11. Apply script encryption if requested - always do this last
        if self.config.get('script_encrypt', False):
            self.logger.info("Encrypting entire PowerShell script...")
            if is_verbose:
                self.logger.info("Using SecureString to encrypt the entire script with a random key")
                
            gen_launcher = self.config.get('generate_launcher', True)
            self.script_encryptor = PowerShellScriptEncryptor(generate_launcher=gen_launcher)
            self.obfuscated_code = self.script_encryptor.transform(self.obfuscated_code)
            self._update_stats(self.script_encryptor.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                key_length = self.stats.get("encryption_key_length", 0)
                self.logger.info(f"Encrypted script with a {key_length * 8}-bit key and generated a launcher")
        
        # Record processing time
        processing_time = time.time() - start_time
        self.stats['processing_time'] = processing_time
        
        if not obfuscation_applied:
            self.logger.warning("No obfuscation methods were applied. Output will be identical to input.")
        elif is_verbose:
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
                
            secure_obfuscator = ObfuscateWithSecureString()
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
            encode_blocks = self.config.get('base64_blocks', True)
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
            transformed = base64_encoder.transform(transformed)
            
            if is_verbose:
                if base64_encoder.stats.get('encoded_full_script', False):
                    logger.info("Encoded the entire script with Base64")
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