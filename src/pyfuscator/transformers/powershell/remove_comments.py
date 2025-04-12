"""
Module for removing comments from PowerShell code.
"""

import re


class RemoveComments:
    """
    Transformer that removes all comments from PowerShell code.
    This includes both single-line and block comments.
    """

    def __init__(self):
        self.removed_comment_count = 0
        self.removed_comment_chars = 0

    def transform(self, code):
        """
        Remove all PowerShell comments from the code.

        Args:
            code (str): PowerShell code

        Returns:
            str: Code with comments removed
        """
        # Count original comment chars
        orig_code_len = len(code)
        
        # Remove multi-line comments (<# ... #>)
        code = re.sub(r'<#.*?#>', '', code, flags=re.DOTALL)
        
        # Remove single-line comments (# ...)
        lines = []
        for line in code.split('\n'):
            # Check if there's a comment in this line
            comment_pos = line.find('#')
            if comment_pos >= 0:
                # Make sure it's not inside a string
                in_string = False
                in_double_quotes = False
                i = 0
                
                while i < comment_pos:
                    if line[i] == "'" and not in_double_quotes:
                        in_string = not in_string
                    elif line[i] == '"' and not in_string:
                        in_double_quotes = not in_double_quotes
                    i += 1
                
                if not in_string and not in_double_quotes:
                    line = line[:comment_pos]
            
            lines.append(line)
        
        # Reassemble the code
        result = '\n'.join(lines)
        
        # Count removed chars
        self.removed_comment_chars = orig_code_len - len(result)
        
        # Count comments - this is approximate
        self.removed_comment_count = len(re.findall(r'<#.*?#>', code, flags=re.DOTALL)) + \
                                    len(re.findall(r'#[^\n]*', code))
        
        return result
    
    def get_stats(self):
        """
        Get statistics about removed comments.
        
        Returns:
            dict: Statistics about removed comments
        """
        return {
            "removed_comment_count": self.removed_comment_count,
            "removed_comment_chars": self.removed_comment_chars
        } 