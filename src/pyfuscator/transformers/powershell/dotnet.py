"""
PowerShell .NET method-based obfuscation transformer.
"""
import re
import random
from typing import Match, List, Tuple, Dict

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class UseDotNetMethods:
    """Transformer that uses .NET methods to obfuscate PowerShell script components."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.count = 0  # Track number of strings transformed
        
        # .NET methods for string operations
        self.string_methods = [
            ("[String]::Concat", 2, 5),  # method, min args, max args
            ("[String]::Format", 2, 4),
            ("[String]::Join", 2, 2),
            ("[string]::new", 1, 3)
        ]
        
        # .NET string instance methods to use
        self.instance_methods = [
            "Replace", "Substring", "ToUpper", "ToLower", "Trim"
        ]
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script using .NET methods.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content using .NET methods
        """
        self.count = 0
        
        # Find string literals that are good candidates for transformation
        # This pattern focuses on longer strings and ignores already processed ones
        # Complex operations use string literals with length > 10 characters
        pattern = r'(?<![\+\'"])("(?:[^"\\]|\\.){10,}"|\'(?:[^\'\\]|\\.){10,}\')(?![\+])'
        
        def replace_string(match: Match) -> str:
            """Replace string with .NET method calls."""
            original = match.group(1)
            # Skip already obfuscated or special strings
            if ("[String]" in original or ".NET" in original or 
                "System." in original or "$" in original):
                return original
                
            self.count += 1
            return self._obfuscate_with_dotnet(original)
        
        transformed = re.sub(pattern, replace_string, content)
        
        # Also obfuscate command invocations (e.g., Invoke-Expression)
        cmdlet_pattern = r'(?<!["\'])(?<!\$)(Invoke-(?:Expression|Command|WebRequest))(?!["\'])'
        
        def replace_cmdlet(match: Match) -> str:
            """Replace cmdlet name with .NET-based construction."""
            cmdlet = match.group(1)
            self.count += 1
            return self._obfuscate_cmdlet(cmdlet)
        
        transformed = re.sub(cmdlet_pattern, replace_cmdlet, transformed)
        
        logger.info(f"Applied .NET method obfuscation to {self.count} elements in PowerShell script")
        return transformed
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about .NET method obfuscation.
        
        Returns:
            Dict with statistics about elements obfuscated with .NET methods
        """
        return {
            "dotnet_methods": self.count
        }
    
    def _obfuscate_with_dotnet(self, string_literal: str) -> str:
        """
        Obfuscate a string literal using .NET methods.
        
        Args:
            string_literal: The string literal to obfuscate
            
        Returns:
            Obfuscated string using .NET methods
        """
        # Extract the actual string content
        quote_char = string_literal[0]
        string_content = string_literal[1:-1]
        
        # Choose obfuscation strategy
        strategy = random.randint(1, 5)
        
        if strategy == 1:
            # Use String::Concat with character arrays
            chars = []
            for c in string_content:
                chars.append(f"[char]{ord(c)}")
            return f"[String]::Concat({', '.join(chars)})"
        
        elif strategy == 2:
            # Use String::Format with substitution parameters
            parts = []
            format_args = []
            current_part = ""
            
            for i, c in enumerate(string_content):
                if i % 5 == 0 and i > 0:
                    parts.append(current_part)
                    format_args.append(f"'{current_part}'")
                    current_part = ""
                current_part += c
            
            # Add the last part
            if current_part:
                parts.append(current_part)
                format_args.append(f"'{current_part}'")
            
            # Create format string with placeholders
            format_string = "".join(["{" + str(i) + "}" for i in range(len(parts))])
            
            return f"[String]::Format('{format_string}', {', '.join(format_args)})"
        
        elif strategy == 3:
            # Split the string and use String::Join
            parts = self._split_string(string_content, random.randint(2, 4))
            quoted_parts = [f"'{part}'" for part in parts]
            
            # Choose a separator (could be empty or a character)
            separator = random.choice(["''", "' '", "','", "';'", "'.'"])
            
            # Create and join array
            array_elements = ",".join(quoted_parts)
            return f"[String]::Join({separator}, @({array_elements}))"
        
        elif strategy == 4:
            # Use a combination of string instance methods
            var_name = f"${random_name(6)}"
            operations = []
            
            # Start with the full string
            operations.append(f"{var_name} = '{string_content}'")
            
            # Apply a few transformations to be then reversed
            num_ops = random.randint(2, 4)
            
            # Keep track of transformations to reverse them later
            transformations = []
            
            for _ in range(num_ops):
                method = random.choice(self.instance_methods)
                
                if method == "Replace":
                    # Replace a character temporarily
                    orig_char = random.choice(string_content)
                    new_char = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
                    operations.append(f"{var_name} = {var_name}.Replace('{orig_char}', '{new_char}')")
                    transformations.append(("Replace", new_char, orig_char))
                
                elif method == "Substring":
                    # Take substring and note the part removed
                    start = random.randint(0, min(5, len(string_content)-1))
                    operations.append(f"{var_name} = {var_name}.Substring({start})")
                    transformations.append(("Substring", start, string_content[:start]))
                
                elif method == "ToUpper":
                    operations.append(f"{var_name} = {var_name}.ToUpper()")
                    transformations.append(("ToUpper", None, None))
                
                elif method == "ToLower":
                    operations.append(f"{var_name} = {var_name}.ToLower()")
                    transformations.append(("ToLower", None, None))
                
                elif method == "Trim":
                    operations.append(f"{var_name} = {var_name}.Trim()")
                    transformations.append(("Trim", None, None))
            
            # Now reverse the transformations
            for transform_type, param1, param2 in reversed(transformations):
                if transform_type == "Replace":
                    operations.append(f"{var_name} = {var_name}.Replace('{param1}', '{param2}')")
                elif transform_type == "Substring":
                    operations.append(f"{var_name} = '{param2}' + {var_name}")
                elif transform_type == "ToUpper":
                    operations.append(f"{var_name} = {var_name}.ToLower()")
                elif transform_type == "ToLower":
                    operations.append(f"{var_name} = {var_name}.ToUpper()")
                elif transform_type == "Trim":
                    pad = "' '" * random.randint(1, 3)
                    operations.append(f"{var_name} = {pad} + {var_name} + {pad}")
            
            # Return the script block with the result variable
            operations_str = "\n".join(operations)
            return f"(& {{ {operations_str}; {var_name} }})"
        
        else:  # strategy == 5
            # Use String constructor with various approaches
            approach = random.randint(1, 3)
            
            if approach == 1:
                # Char array constructor
                chars = [str(ord(c)) for c in string_content]
                return f"[string]::new([char[]]@({','.join(chars)}))"
            
            elif approach == 2:
                # Repeated character constructor (for patterns)
                unique_chars = set(string_content)
                if len(unique_chars) == 1:
                    char = list(unique_chars)[0]
                    return f"[string]::new('{char}', {len(string_content)})"
                else:
                    # Choose a special character that's unlikely to be in the string
                    pad_char = '*'
                    if pad_char in string_content:
                        pad_char = '#'
                    
                    # Pad and then remove
                    padded = (pad_char * 5) + string_content + (pad_char * 5)
                    return f"([string]::new('{pad_char}', 5) + '{string_content}' + [string]::new('{pad_char}', 5)).Trim('{pad_char}')"
            
            else:  # approach == 3
                # String manipulation with StringBuilder
                return f"""(& {{
    $sb = New-Object System.Text.StringBuilder
    $null = $sb.Append('{string_content}')
    $sb.ToString()
}})"""
    
    def _obfuscate_cmdlet(self, cmdlet: str) -> str:
        """
        Obfuscate a PowerShell cmdlet name using .NET.
        
        Args:
            cmdlet: The cmdlet name to obfuscate
            
        Returns:
            Obfuscated cmdlet construction
        """
        parts = cmdlet.split('-')
        verb = parts[0]
        noun = parts[1]
        
        # Choose obfuscation method
        method = random.randint(1, 3)
        
        if method == 1:
            # Use String::Concat
            return f"[String]::Concat('{verb}', '-', '{noun}')"
        
        elif method == 2:
            # Use character arrays
            chars = []
            for c in cmdlet:
                chars.append(f"[char]{ord(c)}")
            return f"[String]::new([char[]]@({', '.join(chars)}))"
        
        else:  # method == 3
            # Use String::Format
            return f"[String]::Format('{{0}}-{{1}}', '{verb}', '{noun}')"
    
    def _split_string(self, string: str, num_parts: int) -> List[str]:
        """
        Split a string into a specified number of random-sized parts.
        
        Args:
            string: The string to split
            num_parts: Number of parts to split into
            
        Returns:
            List of string parts
        """
        if num_parts <= 1 or len(string) <= num_parts:
            return [string]
            
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