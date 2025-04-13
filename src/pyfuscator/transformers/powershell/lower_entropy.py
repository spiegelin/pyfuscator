"""
PowerShell entropy reduction transformer.

This transformer aims to reduce the entropy of PowerShell scripts by:
1. Inserting random spaces after certain characters
2. Substituting common commands with their aliases
3. Reordering non-critical blocks like comments
"""
import random
import re
from typing import Dict, Any

from pyfuscator.core.transformer import Transformer
from pyfuscator.log_utils import logger

class LowerEntropy(Transformer):
    """Transformer that reduces entropy of PowerShell scripts."""

    def __init__(self):
        """Initialize the entropy reducer transformer."""
        super().__init__()
        self.stats = {
            'spaces_inserted': 0,
            'aliases_substituted': 0,
            'blocks_reordered': 0,
            'case_variations': 0
        }

    def transform(self, content: str) -> str:
        """
        Apply the entropy reduction transformation.
        
        Args:
            content: The input PowerShell script
            
        Returns:
            The transformed PowerShell script with lower entropy
        """
        if not content.strip():
            logger.warning("Empty content provided to LowerEntropy transformer")
            return content
            
        # Track the original content length
        original_length = len(content)
        
        # Apply transformations
        content = self._random_space_insertion(content)
        content = self._substitute_aliases(content)
        content = self._random_case_variation(content)
        content = self._reorder_noncritical_blocks(content)
        
        # Update stats
        self.stats['char_length_before'] = original_length
        self.stats['char_length_after'] = len(content)
        
        return content
        
    def _random_space_insertion(self, text: str) -> str:
        """
        Insert random spaces after certain characters.
        
        Args:
            text: The input text
            
        Returns:
            The text with random spaces inserted
        """
        result = ''
        spaces_inserted = 0
        
        for ch in text:
            result += ch
            if ch in [';', '{', '}', '|', '(', ')', ',']:
                spaces = random.randint(0, 2)
                result += ' ' * spaces
                spaces_inserted += spaces
                
        self.stats['spaces_inserted'] = spaces_inserted
        return result
        
    def _substitute_aliases(self, text: str) -> str:
        """
        Substitute common PowerShell commands with their aliases.
        
        Args:
            text: The input text
            
        Returns:
            The text with commands replaced by aliases
        """
        # Common PowerShell command to alias mappings
        substitutions = {
            # Core cmdlets
            r'\bGet-Process\b': 'gps',
            r'\bGet-Service\b': 'gsv',
            r'\bGet-Content\b': 'gc',
            r'\bSet-Content\b': 'sc',
            r'\bGet-ChildItem\b': random.choice(['gci', 'dir', 'ls']),
            r'\bWrite-Output\b': random.choice(['echo', 'write']),
            r'\bForEach-Object\b': '%',
            r'\bWhere-Object\b': '?',
            r'\bSelect-Object\b': 'select',
            r'\bInvoke-Expression\b': 'iex',
            r'\bInvoke-Command\b': 'icm',
            
            # Navigation and file system
            r'\bSet-Location\b': random.choice(['cd', 'sl']),
            r'\bGet-Location\b': random.choice(['pwd', 'gl']),
            r'\bCopy-Item\b': random.choice(['copy', 'cp', 'cpi']),
            r'\bMove-Item\b': random.choice(['move', 'mv', 'mi']),
            r'\bRemove-Item\b': random.choice(['del', 'erase', 'rd', 'ri', 'rm']),
            r'\bRename-Item\b': random.choice(['ren', 'rni']),
            r'\bTest-Path\b': 'test',
            
            # Management cmdlets
            r'\bGet-Alias\b': 'gal',
            r'\bImport-Module\b': 'ipmo',
            r'\bExport-Module\b': 'epmo',
            r'\bGet-Module\b': 'gmo',
            r'\bNew-Item\b': 'ni',
            r'\bAdd-Content\b': 'ac',
            r'\bGet-History\b': random.choice(['history', 'ghy']),
            r'\bGet-Command\b': 'gcm',
            r'\bGet-Help\b': random.choice(['help', 'man']),
            r'\bMeasure-Object\b': 'measure',
            
            # Comparison and filtering
            r'\bCompare-Object\b': random.choice(['compare', 'diff']),
            r'\bGroup-Object\b': 'group',
            r'\bSort-Object\b': 'sort',
            r'\bTee-Object\b': 'tee',
            
            # Output formatting
            r'\bFormat-List\b': 'fl',
            r'\bFormat-Table\b': 'ft',
            r'\bFormat-Wide\b': 'fw',
            r'\bOut-Host\b': 'oh',
            r'\bOut-File\b': 'of',
            r'\bOut-String\b': 'os',
            r'\bOut-GridView\b': 'ogv',
            
            # Others
            r'\bConvertTo-Html\b': 'ConvertTo-Html',
            r'\bConvertTo-Csv\b': 'ConvertTo-Csv',
            r'\bExport-Csv\b': 'epcsv',
            r'\bImport-Csv\b': 'ipcsv',
            r'\bNew-Object\b': 'new',
            r'\bNew-TimeSpan\b': 'nts',
            r'\bStart-Process\b': random.choice(['saps', 'start']),
            r'\bStart-Service\b': 'sasv',
            r'\bStop-Process\b': random.choice(['spps', 'kill']),
            r'\bStop-Service\b': 'spsv',
            r'\bWait-Process\b': 'wait',
            r'\bClear-Host\b': random.choice(['cls', 'clear'])
        }
        
        aliases_count = 0
        for pattern, replacement in substitutions.items():
            # Only substitute with some probability to add randomness
            if random.random() < 0.7:  # 70% chance to substitute
                new_text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if new_text != text:
                    aliases_count += len(re.findall(pattern, text, re.IGNORECASE))
                    text = new_text
                    
        self.stats['aliases_substituted'] = aliases_count
        return text
        
    def _random_case_variation(self, text: str) -> str:
        """
        Randomly change the case of characters in cmdlets and aliases.
        
        Args:
            text: The input text
            
        Returns:
            The text with random case variations
        """
        # Common PowerShell cmdlets and keywords to apply case variation to
        keywords = [
            r'\b(function)\b', r'\b(param)\b', r'\b(if)\b', r'\b(else)\b', r'\b(elseif)\b',
            r'\b(while)\b', r'\b(for)\b', r'\b(foreach)\b', r'\b(switch)\b', r'\b(try)\b',
            r'\b(catch)\b', r'\b(finally)\b', r'\b(return)\b', r'\b(exit)\b', r'\b(begin)\b',
            r'\b(process)\b', r'\b(end)\b', r'\b(throw)\b', r'\b(continue)\b', r'\b(break)\b',
            r'\b(do)\b', r'\b(until)\b', r'\b(workflow)\b', r'\b(configuration)\b', r'\b(class)\b',
            r'\b(enum)\b', r'\b(using)\b', r'\b(var)\b', r'\b(hidden)\b', r'\b(static)\b',
            r'\b(from)\b', r'\b(where)\b', r'\b(select)\b', r'\b(group)\b', r'\b(by)\b'
        ]
        
        case_variations = 0
        for keyword in keywords:
            # Find all instances of the keyword
            matches = re.finditer(keyword, text, re.IGNORECASE)
            for match in matches:
                # 40% chance to randomize case for each match
                if random.random() < 0.4:
                    word = match.group(0)
                    randomized = ''.join(c.upper() if random.random() < 0.5 else c.lower() for c in word)
                    text = text[:match.start()] + randomized + text[match.end():]
                    case_variations += 1
        
        self.stats['case_variations'] = case_variations
        return text
        
    def _reorder_noncritical_blocks(self, text: str) -> str:
        """
        Reorder non-critical blocks like comments.
        
        Args:
            text: The input text
            
        Returns:
            The text with some blocks reordered
        """
        # Split the script into blocks by blank lines
        blocks = text.split('\n\n')
        blocks_reordered = 0
        
        for i in range(len(blocks)):
            # Only reorder blocks that are likely comments or non-critical
            # (Contains '#' and has multiple lines)
            if random.random() < 0.3 and len(blocks[i].splitlines()) > 2 and '#' in blocks[i]:
                lines = blocks[i].splitlines()
                comment_lines = [line for line in lines if line.strip().startswith('#')]
                code_lines = [line for line in lines if not line.strip().startswith('#')]
                
                # Only shuffle comment lines to avoid breaking code
                random.shuffle(comment_lines)
                
                # Reconstruct the block with shuffled comments and original code
                blocks[i] = "\n".join(comment_lines + code_lines)
                blocks_reordered += 1
                
        self.stats['blocks_reordered'] = blocks_reordered
        return "\n\n".join(blocks)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the transformation.
        
        Returns:
            Dictionary with transformation statistics
        """
        return self.stats 