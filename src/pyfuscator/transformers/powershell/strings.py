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
        self.string_pattern = re.compile(
            r'(?<![`\\])(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
        )

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

            # Skip strings in PowerShell attribute arguments like ValidateSet
            if self._is_attribute_argument(transformed, match.start()):
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
        return content[pos-1] == '-' if pos > 0 else False

    
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
    
    def _is_attribute_argument(self, content: str, pos: int) -> bool:
        """
        Check if a string at the given position is within a PowerShell attribute argument.
        
        Args:
            content: The PowerShell script content
            pos: Position of the string in the content
            
        Returns:
            True if the string is within an attribute argument, False otherwise
        """
        # Look for attribute patterns before the string position
        # This covers cases like [ValidateSet("Low", "Medium", "High")]
        prefix = content[max(0, pos-100):pos]
        
        # Check for common attribute patterns
        attribute_patterns = [
            r'\[ValidateSet\(\s*',          # ValidateSet attribute
            r'\[Parameter\s*\(',            # Parameter attribute
            r'\[ValidatePattern\s*\(',      # ValidatePattern attribute
            r'\[Alias\s*\(',                # Alias attribute
            r'\[ValidateRange\s*\(',        # ValidateRange attribute
            r'\[ValidateScript\s*\(',       # ValidateScript attribute
            r'\[ValidateNotNull',           # ValidateNotNull attribute
            r'\[ValidateNotNullOrEmpty'     # ValidateNotNullOrEmpty attribute
        ]
        
        # Check if any attribute pattern precedes the string
        for pattern in attribute_patterns:
            if re.search(pattern, prefix):
                # Additional check for proper attribute argument context
                # Count parentheses to ensure we're inside an attribute argument list
                open_parens = prefix.count('(')
                close_parens = prefix.count(')')
                if open_parens > close_parens:  # We're inside an attribute argument
                    return True
        
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
        # Comment out format operator since it breaks the script when used with other techniques, 
        # too much effort to fix it, will do it later (probably never)

        # Commented out the hex_encode_technique since it is getting too many detections
        techniques = [
            self._format_operator_technique, # 2 VT detections (powercat)
            lambda x: self._concatenation_technique(x, quote_char), # 3 VT detections (powercat)
            self._char_array_technique, # 2 VT detections (powercat)
            #self._hex_encode_technique, # 11 VT detections (powercat)
            lambda x: self._mixed_technique(x, quote_char)
        ]
        
        technique = random.choice(techniques)
        return technique(inner_content)
        
    
    def _format_operator_technique(self, string_content: str) -> str:
        char_codes = [f"[char]0x{ord(c):02x}" for c in string_content]
        return "(-join (" + " + ".join(char_codes) + "))"
    
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
        i = 0
        while i < len(string_content):
            chunk_size = min(random.randint(1, 3), len(string_content) - i)
            chunk = string_content[i:i+chunk_size]
            part = "+".join([f"[char]0x{ord(c):02x}" for c in chunk])
            parts.append(f"({part})")
            i += chunk_size
        return "(-join (" + " + ".join(parts) + "))"
    
    def _char_array_technique(self, string_content: str) -> str:
        """
        Obfuscate a string using character array joining.
        
        Args:
            string_content: The string content without quotes
            
        Returns:
            Obfuscated string expression
        """
        # Convert to character array, escaping single quotes correctly
        char_elements = []
        for c in string_content:
            # Convert each character to [char]0xXX format
            hex_code = f"{ord(c):02x}"
            char_elements.append(f"[char]0x{hex_code}")
        return "(-join @(" + ",".join(char_elements) + "))"
    
    def _hex_encode_technique(self, string_content: str) -> str:
        """
        Encode a string segment to hexadecimal and create a PowerShell expression to decode it.
        
        Args:
            string_content: The string segment to encode
            
        Returns:
            PowerShell expression to reconstruct the segment from hex
        """
        # Encode the segment to hexadecimal
        utf16_bytes = string_content.encode('utf-16le')
        if len(utf16_bytes) % 2 != 0:
            utf16_bytes += b'\x00'  # Pad to even length
        hex_values = [f"0x{byte:02x}" for byte in utf16_bytes]
        return "([System.Text.Encoding]::Unicode.GetString([byte[]]@({})))".format(",".join(hex_values))

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
        num_parts = random.randint(2, min(4, len(string_content)))
        split_points = sorted(random.sample(range(1, len(string_content)), num_parts - 1))
        split_points = [0] + split_points + [len(string_content)]
        parts = []
        for i in range(len(split_points) - 1):
            part = string_content[split_points[i]:split_points[i+1]]
            technique = random.choice([
                self._char_array_technique,
                lambda x: self._concatenation_technique(x, quote_char)
                #self._hex_encode_technique # Too many VT detections
            ])
            parts.append(technique(part))
        return "(-join (" + " + ".join(parts) + "))"
    
    def _split_string(self, string: str, num_parts: int) -> List[str]:
        """
        Split a string into a specified number of random-sized parts.
        
        Args:
            string: The string to split
            num_parts: Number of parts to split into
            
        Returns:
            List of string parts
        """
        parts = []
        current = []
        in_escape = False
        for c in string:
            if c == '\\' and not in_escape:
                in_escape = True
            else:
                in_escape = False
            current.append(c)
            if len(current) >= 3 and not in_escape:
                parts.append(''.join(current))
                current = []
        if current:
            parts.append(''.join(current))
        return parts
    
    def _is_attribute_argument(self, content: str, pos: int) -> bool:
        """Skip strings in parameter attributes"""
        context = content[max(0, pos-100):pos+100]
        return any(
            re.search(rf'\[{attr}\s*\(', context)
            for attr in ['alias', 'ValidateSet', 'Parameter']
        )

    def _contains_variables(self, string_content: str) -> bool:
        """Detect PowerShell variables more accurately"""
        # check for escape sequences like `n, `t, etc.
        if re.search(r'`[a-zA-Z]', string_content):
            return True
        if string_content.startswith('"'):
            return bool(re.search(r'\$[\w{]', string_content))
        return False