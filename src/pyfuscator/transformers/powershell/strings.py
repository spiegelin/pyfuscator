"""
PowerShell string obfuscation transformer.
"""
import re
import random
from typing import List, Tuple, Dict, Any

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger

class ObfuscateStrings(Transformer):
    """Transformer that obfuscates strings in PowerShell scripts using various techniques."""
    
    def __init__(self, split_min: int = 2, split_max: int = 4, obfuscation_probability: float = 0.7):
        """
        Initialize the transformer.
        
        Args:
            split_min: Minimum number of parts to split strings into
            split_max: Maximum number of parts to split strings into
            obfuscation_probability: Probability that a given string will be obfuscated (0.0-1.0)
        """
        super().__init__()
        self.split_min = split_min
        self.split_max = split_max
        self.obfuscation_probability = obfuscation_probability
        
        self.stats = {
            "strings_obfuscated": 0
        }
        
        # Regex to find string literals with consideration for escape sequences
        # This handles both single and double quoted strings
        self.string_pattern = re.compile(r'(?<!`)(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')')
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by obfuscating strings.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with obfuscated strings
        """
        self.stats["strings_obfuscated"] = 0
        
        if not content.strip():
            return content
        
        transformed = content
        string_matches = list(self.string_pattern.finditer(transformed))
        
        # Process strings in reverse order to maintain correct positions
        for match in sorted(string_matches, key=lambda m: m.start(), reverse=True):
            string_content = match.group(0)
            
            # Don't process empty strings or very short strings
            if len(string_content) <= 3:
                continue
                
            # Skip strings that are likely to be part of cmdlet names or parameter names
            if self._is_likely_cmdlet_param(transformed, match.start()):
                continue
            
            # Skip strings containing PowerShell variables ($var, ${var}, etc.)
            if self._contains_variables(string_content):
                continue
                
            # Apply obfuscation with specified probability
            if random.random() > self.obfuscation_probability:
                continue
                
            # Obfuscate the string using varied techniques
            obfuscated_string = self._obfuscate_string(string_content)
            
            # Replace the string with its obfuscated version
            start, end = match.span(0)
            transformed = transformed[:start] + obfuscated_string + transformed[end:]
            self.stats["strings_obfuscated"] += 1
        
        if self.stats["strings_obfuscated"] > 0:
            logger.info(f"Obfuscated {self.stats['strings_obfuscated']} string literals in PowerShell script")
            
        return transformed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about obfuscated strings.
        
        Returns:
            Dict with statistics about obfuscated strings
        """
        return self.stats
    
    def _is_likely_cmdlet_param(self, content: str, pos: int) -> bool:
        """
        Check if a string at the given position is likely part of a cmdlet parameter.
        
        Args:
            content: The PowerShell script content
            pos: Position of the string in the content
            
        Returns:
            True if the string is likely a cmdlet parameter, False otherwise
        """
        # Check if the string is preceded by a dash and space or tab
        prefix = content[max(0, pos-10):pos].strip()
        return prefix.endswith('-')
    
    def _contains_variables(self, string_content: str) -> bool:
        """
        Check if a string contains PowerShell variables that should not be obfuscated.
        
        Args:
            string_content: The string to check
            
        Returns:
            True if the string contains variables, False otherwise
        """
        # Only check double-quoted strings which can contain variables
        if string_content.startswith('"') and string_content.endswith('"'):
            # Look for $var, ${var}, or $( ) constructs
            # This regex matches PowerShell variable patterns
            var_pattern = r'\$[\w\d_]+|\$\{[\w\d_]+\}|\$\(.*?\)'
            return bool(re.search(var_pattern, string_content))
        return False
    
    def _obfuscate_string(self, string_content: str) -> str:
        """
        Obfuscate a string using various techniques.
        
        Args:
            string_content: The string to obfuscate (including quotes)
            
        Returns:
            Obfuscated string expression
        """
        # Determine quote type (single or double)
        quote_char = string_content[0]
        inner_content = string_content[1:-1]
        
        # Choose an obfuscation technique
        techniques = [
            self._format_operator_technique,
            self._concatenation_technique,
            self._char_array_technique,
            self._hex_encode_technique,
            self._mixed_technique
        ]
        
        technique = random.choice(techniques)
        
        # Apply the chosen technique
        if technique == self._concatenation_technique or technique == self._mixed_technique:
            return technique(inner_content, quote_char)
        elif technique == self._hex_encode_technique:
            return technique(inner_content)
        else:
            return technique(inner_content)
    
    def _format_operator_technique(self, string_content: str) -> str:
        """
        Obfuscate a string using the format operator.
        
        Args:
            string_content: The string content without quotes
            
        Returns:
            Obfuscated string expression
        """
        format_parts = []
        values = []
        
        # Create format placeholders and values
        i = 0
        while i < len(string_content):
            # Determine segment length (1-3 characters)
            segment_len = min(random.randint(1, 3), len(string_content) - i)
            segment = string_content[i:i+segment_len]
            
            # Add format placeholder and value
            format_parts.append("{" + str(len(values)) + "}")
            values.append(f"'{segment}'")
            
            i += segment_len
        
        # Build the format expression
        format_string = f"'{''.join(format_parts)}'" if len(format_parts) > 1 else f"'{format_parts[0]}'"
        values_string = ','.join(values)
        
        return f"($({format_string} -f {values_string}))"
    
    def _concatenation_technique(self, string_content: str, quote_char: str) -> str:
        """
        Obfuscate a string using string concatenation.
        
        Args:
            string_content: The string content without quotes
            quote_char: The quote character used (single or double)
            
        Returns:
            Obfuscated string expression
        """
        parts = []
        
        # Split the string into random-sized chunks
        i = 0
        while i < len(string_content):
            # Determine chunk size (1-5 characters)
            chunk_size = min(random.randint(1, 5), len(string_content) - i)
            chunk = string_content[i:i+chunk_size]
            
            # Escape quotes if needed
            if quote_char in chunk:
                chunk = chunk.replace(quote_char, f"`{quote_char}")
                
            # Add the chunk
            parts.append(f"{quote_char}{chunk}{quote_char}")
            
            i += chunk_size
        
        # Join the parts with concatenation operators
        return "(" + " + ".join(parts) + ")"
    
    def _char_array_technique(self, string_content: str) -> str:
        """
        Obfuscate a string using character array joining.
        
        Args:
            string_content: The string content without quotes
            
        Returns:
            Obfuscated string expression
        """
        # Convert to character array
        char_array = [f"'{c}'" if c != "'" else "'`'''" for c in string_content]
        
        # Join the array
        return f"([char[]]({','.join(char_array)}) -join '')"
    
    def _hex_encode_technique(self, string_content: str) -> str:
        """
        Encode a string segment to hexadecimal and create a PowerShell expression to decode it.
        
        Args:
            string_content: The string segment to encode
            
        Returns:
            PowerShell expression to reconstruct the segment from hex
        """
        # Encode the segment to hexadecimal
        hex_seg = string_content.encode('utf-8').hex()
        
        # Create a PowerShell expression that rebuilds the string from hex values
        rebuilt = '+'.join(f'[char](0x{hex_seg[i:i+2]})' for i in range(0, len(hex_seg), 2))
        return f"({rebuilt})"
    
    def _mixed_technique(self, string_content: str, quote_char: str) -> str:
        """
        Obfuscate a string using a mix of techniques.
        
        Args:
            string_content: The string content without quotes
            quote_char: The quote character used (single or double)
            
        Returns:
            Obfuscated string expression
        """
        # Split into 2-3 main parts
        num_parts = random.randint(2, min(3, len(string_content)))
        part_size = len(string_content) // num_parts
        
        parts = []
        for i in range(num_parts):
            start_idx = i * part_size
            end_idx = len(string_content) if i == num_parts - 1 else (i + 1) * part_size
            part = string_content[start_idx:end_idx]
            
            # Apply a random technique to each part
            technique = random.randint(1, 4)
            if technique == 1 and len(part) > 1:
                parts.append(self._format_operator_technique(part))
            elif technique == 2:
                parts.append(self._concatenation_technique(part, quote_char))
            elif technique == 3:
                parts.append(self._char_array_technique(part))
            else:
                parts.append(self._hex_encode_technique(part))
        
        # Join the parts
        return "(" + " + ".join(parts) + ")"
    
    def _split_string(self, string: str, num_parts: int) -> List[str]:
        """
        Split a string into a specified number of random-sized parts.
        
        Args:
            string: The string to split
            num_parts: Number of parts to split into
            
        Returns:
            List of string parts
        """
        if num_parts <= 1:
            return [string]
            
        # For shorter strings, split more evenly
        if len(string) < 10:
            # Calculate approximate segment size
            seg_size = max(1, len(string) // num_parts)
            
            # Split the string into segments
            parts = []
            for i in range(0, len(string), seg_size):
                parts.append(string[i:i+seg_size])
            
            return parts
            
        # Generate random split points
        string_len = len(string)
        split_points = sorted(random.sample(range(1, string_len), num_parts - 1))
        
        # Split the string at those points
        parts = []
        start = 0
        for point in split_points:
            parts.append(string[start:point])
            start = point
        parts.append(string[start:])
        
        return parts 