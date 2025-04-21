"""
PowerShell obfuscation coordinator.
"""
import time
import re
import random

from pyfuscator.log_utils import logger
from pyfuscator.transformers.powershell.identifiers import RenameIdentifiers
from pyfuscator.transformers.powershell.strings import ObfuscateStrings
from pyfuscator.transformers.powershell.concat import CommandTokenizer
from pyfuscator.transformers.powershell.junk import InsertJunkCode
from pyfuscator.transformers.powershell.dotnet import UseDotNetMethods
from pyfuscator.transformers.powershell.securestring import SecureStringTransformer
from pyfuscator.transformers.powershell.remove_comments import RemoveComments
from pyfuscator.transformers.powershell.lower_entropy import LowerEntropy
from pyfuscator.transformers.powershell.base64 import Base64Encoder
from pyfuscator.transformers.powershell.script_encryptor import PowerShellScriptEncryptor
from pyfuscator.encryption.methods import (
    encryption_method_1, encryption_method_2, 
    encryption_method_3, encryption_method_4,
    encryption_method_5
)

class PowerShellObfuscator:
    """Main class for PowerShell obfuscation."""

    def __init__(self, config=None):
        """Initialize the PowerShell obfuscator.

        Args:
            config: Configuration options for the obfuscator.
                   Can be a dictionary, ObfuscationConfig, or any object with a get() method.
        """
        self.config = config or {}
        # If config doesn't have a get method but has __getitem__, create a wrapper get method
        if not hasattr(self.config, 'get') and hasattr(self.config, '__getitem__'):
            original_config = self.config
            # Create a dictionary-like wrapper with a get method
            self.config = type('ConfigWrapper', (), {
                'get': lambda self, key, default=None: original_config[key] if key in original_config else default,
                '__getitem__': lambda self, key: original_config[key]
            })()
        
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
        self.comment_remover = None
        self.entropy_reducer = None
        self.base64_encoder = None
        self.script_encryptor = None
        self.string_divider = None
        

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
        
        # 9. Apply Base64 encoding if specified
        if self.config.get('base64_encode', False) or self.config.get('base64_commands', False) or self.config.get('base64_full', False):
            if is_verbose:
                self.logger.info("Applying Base64 encoding to PowerShell script")
            
            # Configure the encoder
            encode_blocks = self.config.get('base64_encode', False)
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
            
            # Create the encoder with the correct configuration
            base64_encoder = Base64Encoder(
                encode_blocks=encode_blocks,
                encode_full=encode_full,
                encode_individual=encode_cmds
            )
            
            # Apply the transformation
            prev_code = self.obfuscated_code
            self.obfuscated_code = base64_encoder.transform(self.obfuscated_code)
            
            # If nothing was encoded and full script encoding was requested, force it
            if prev_code == self.obfuscated_code and encode_full:
                if is_verbose:
                    self.logger.info("Forcing full script Base64 encoding")
                self.obfuscated_code = base64_encoder._encode_full_script(prev_code)
                base64_encoder.stats["encoded_full_script"] = True
            
            # If nothing was encoded but blocks or commands encoding was requested, 
            # try a fallback approach to ensure something gets encoded
            if prev_code == self.obfuscated_code and (encode_blocks or encode_cmds):
                if is_verbose:
                    self.logger.info("No commands found for encoding, applying fallback encoding")
                
                # Create a simple fallback that encodes a small part of the script
                lines = self.obfuscated_code.split('\n')
                if len(lines) > 5:
                    # Find some content to encode (non-empty lines)
                    content_lines = [i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('#')]
                    if content_lines:
                        # Select a random line to encode
                        line_idx = random.choice(content_lines)
                        line = lines[line_idx]
                        
                        # Only encode if the line isn't too complex
                        if len(line) < 100 and not re.search(r'function|param\s*\(|\{|\}|\$\(|\$\{', line):
                            # Wrap it as a simple Write-Output for Base64 encoding
                            encoded_line = base64_encoder._encode_base64(f'Write-Output "{line.strip()}"')
                            lines[line_idx] = encoded_line
                            self.obfuscated_code = '\n'.join(lines)
                            base64_encoder.stats["commands_encoded"] = 1
                            
                            if is_verbose:
                                self.logger.info("Applied fallback Base64 encoding to ensure some content is encoded")
            
            # Update stats
            self._update_stats(base64_encoder.get_stats())
            obfuscation_applied = True
            
            if is_verbose:
                if base64_encoder.stats.get('encoded_full_script', False):
                    self.logger.success("Encoded entire script with Base64")
                else:
                    encoded_blocks = self.stats.get('blocks_encoded', 0)
                    encoded_cmds = self.stats.get('commands_encoded', 0)
                    self.logger.success(f"Base64 encoded {encoded_blocks} script blocks and {encoded_cmds} commands")
        
        # 10. Apply script encryption if requested
        encryption_layers = self.config.get('script_encrypt', 0)
        if encryption_layers > 0:
            if is_verbose:
                self.logger.success(f"Applying {encryption_layers} layers of encryption")

            # Apply specified number of encryption layers
            self.obfuscated_code = self._apply_encryption_layers(self.obfuscated_code, encryption_layers)

            # Update stats
            self.stats['encryption_layers'] = encryption_layers
            
            # Log success
            self.logger.success(f"Applied {encryption_layers} layers of encryption")
                
            obfuscation_applied = True
        
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
            method = random.randint(2, 4)
            method_name = ["Linear Congruence","XOR with Shuffle Key","RSA-like","Key Array XOR","Triple Layer Cipher"]
            if self.config.get('verbose', False):
                self.logger.info(f"Applying encryption method {method_name[method-1]} (layer {i+1}/{layers})")
            
            if method == 1: # Division by zero? -> Avoid
                code = encryption_method_1(code, "powershell")
            if method == 2:
                code = encryption_method_2(code, "powershell")
            elif method == 3 and i < 3: # If more than 3 layers, use other methods, this is super slow
                code = encryption_method_3(code, "powershell")
            elif method == 4:
                code = encryption_method_4(code, "powershell")
            else: # not yet supported
                code = encryption_method_5(code, "powershell")
            
            if self.config.get('verbose', False):
                self.logger.info(f"Layer {i+1} encryption complete, code size: {len(code)} bytes")
            
        return code

    def _update_stats(self, stats):
        self.stats.update(stats)

    def _tokenize_command(self, command: str) -> str:
        """Obfuscate PowerShell commands using token splitting."""
        # Split the command into parts
        parts = re.split(r'(\W+)', command)
        
        # Handle command arguments properly
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
        
        # Check if no commands were encoded and force encoding something as a fallback
        if self.stats.get('commands_encoded', 0) == 0:
            if is_verbose:
                self.logger.info("No standard commands found for Base64 encoding, applying fallback encoding")
            
            # Create a simple fallback that encodes a small part of the script
            lines = processed_code.split('\n')
            if len(lines) > 5:
                # Find some content to encode (non-empty lines)
                content_lines = [i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('#')]
                if content_lines:
                    # Select a random line to encode
                    line_idx = random.choice(content_lines)
                    line = lines[line_idx]
                    
                    # Only encode if the line isn't too complex
                    if len(line) < 100 and not re.search(r'function|param\s*\(|\{|\}|\$\(|\$\{', line):
                        # Wrap it as a simple Write-Output for Base64 encoding
                        encoded_line = base64_encoder._encode_base64(f'Write-Output "{line.strip()}"')
                        lines[line_idx] = encoded_line
                        processed_code = '\n'.join(lines)
                        self.stats["commands_encoded"] = 1
                        
                        if is_verbose:
                            self.logger.info("Applied fallback Base64 encoding to ensure some content is encoded")
        
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