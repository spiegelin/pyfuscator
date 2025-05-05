"""
PowerShell entropy reduction transformer.

This transformer aims to reduce the entropy of PowerShell scripts by:
1. Inserting random spaces after certain characters (outside strings)
2. Substituting common commands with their aliases
3. Reordering non-critical comment blocks
4. Adding random case variations to keywords
"""

import random
import re
from typing import Dict, Any

class LowerEntropy:
    """Transformer that reduces entropy of PowerShell scripts."""

    def __init__(self):
        self.stats = {
            'spaces_inserted': 0,
            'aliases_substituted': 0,
            'blocks_reordered': 0,
            'case_variations': 0
        }

        # Get all built-in aliases
        # Get-Alias | Group-Object Definition | Sort-Object Name | ForEach-Object {
        #     [PSCustomObject]@{
        #         Command = $_.Name
        #         Aliases = ($_.Group | ForEach-Object { $_.Name }) -join ', '
        #     }
        # }
        self.substitutions = {
            r'\bGet-Process\b': 'gps',
            r'\bGet-Service\b': 'gsv',
            r'\bGet-Content\b': 'gc',
            r'\bSet-Content\b': 'sc',
            r'\bGet-ChildItem\b': random.choice(['gci', 'dir', 'ls']),
            r'\bWrite-Output\b': random.choice(['echo', 'write']),
            # commands with multiple built‑in aliases
            r'\bForEach-Object\b': random.choice(['%', 'foreach']),
            r'\bWhere-Object\b': random.choice(['?', 'where']),
            r'\bSelect-Object\b': 'select',
            r'\bInvoke-Expression\b': 'iex',
            r'\bInvoke-Command\b': 'icm',
            r'\bSet-Location\b': random.choice(['cd', 'chdir', 'sl']),
            r'\bGet-Location\b': random.choice(['gl', 'pwd']),
            r'\bCopy-Item\b': random.choice(['copy', 'cp', 'cpi']),
            r'\bRemove-Item\b': random.choice(['del', 'erase', 'rd', 'ri', 'rm', 'rmdir']),
            r'\bAdd-Content\b': 'ac',
            r'\bAdd-PSSnapIn\b': 'asnp',
            r'\bClear-Content\b': 'clc',
            r'\bClear-History\b': 'clhy',
            r'\bClear-Host\b': random.choice(['clear', 'cls']),
            r'\bClear-Item\b': 'cli',
            r'\bClear-ItemProperty\b': 'clp',
            r'\bClear-Variable\b': 'clv',
            r'\bCompare-Object\b': random.choice(['compare', 'diff']),
            r'\bConnect-PSSession\b': 'cnsn',
            r'\bDisconnect-PSSession\b': 'dnsn',
            r'\bEnable-PSBreakpoint\b': 'ebp',
            r'\bDisable-PSBreakpoint\b': 'dbp',
            r'\bEnter-PSSession\b': 'etsn',
            r'\bExit-PSSession\b': 'exsn',
            r'\bExport-Alias\b': 'epal',
            r'\bExport-Csv\b': 'epcsv',
            r'\bExport-PSSession\b': 'epsn',
            r'\bFormat-Custom\b': 'fc',
            r'\bFormat-Hex\b': 'fhx',
            r'\bFormat-List\b': 'fl',
            r'\bFormat-Table\b': 'ft',
            r'\bFormat-Wide\b': 'fw',
            r'\bGet-Alias\b': 'gal',
            r'\bGet-Clipboard\b': 'gcb',
            r'\bGet-Command\b': 'gcm',
            r'\bGet-ComputerInfo\b': 'gin',
            r'\bGet-History\b': 'h',
            r'\bGet-Item\b': 'gi',
            r'\bGet-ItemProperty\b': 'gp',
            r'\bGet-ItemPropertyValue\b': 'gpv',
            r'\bGet-Job\b': 'gjb',
            r'\bGet-Member\b': 'gm',
            r'\bGet-Module\b': 'gmo',
            r'\bGet-PSBreakpoint\b': 'gbp',
            r'\bGet-PSCallStack\b': 'gcs',
            r'\bGet-PSDrive\b': 'gdr',
            r'\bGet-PSSession\b': 'gsn',
            r'\bGet-PSSnapIn\b': 'gsnp',
            r'\bGet-TimeZone\b': 'gtz',
            r'\bGet-Unique\b': 'gu',
            r'\bGet-WmiObject\b': 'gwmi',
            r'\bGroup-Object\b': 'group',
            r'\bImport-Alias\b': 'ipal',
            r'\bImport-Csv\b': 'ipcsv',
            r'\bImport-Module\b': 'ipmo',
            r'\bImport-PSSession\b': 'ipsn',
            r'\bInvoke-History\b': random.choice(['ihy', 'r']),
            r'\bInvoke-Item\b': 'ii',
            r'\bInvoke-RestMethod\b': 'irm',
            r'\bInvoke-WebRequest\b': random.choice(['curl', 'iwr', 'wget']),
            r'\bInvoke-WMIMethod\b': 'iwmi',
            r'\bMeasure-Object\b': 'measure',
            r'\bmkdir\b': 'md',
            r'\bMove-Item\b': random.choice(['mi', 'move', 'mv']),
            r'\bMove-ItemProperty\b': 'mp',
            r'\bNew-Alias\b': 'nal',
            r'\bNew-Item\b': 'ni',
            r'\bNew-Module\b': 'nmo',
            r'\bNew-PSDrive\b': random.choice(['mount', 'ndr']),
            r'\bNew-PSSession\b': 'nsn',
            r'\bNew-PSSessionConfigurationFile\b': 'npssc',
            r'\bNew-Variable\b': 'nv',
            r'\bOut-GridView\b': 'ogv',
            r'\bOut-Host\b': 'oh',
            r'\bOut-Printer\b': 'lp',
            r'\bPop-Location\b': 'popd',
            r'\bPush-Location\b': 'pushd',
            r'\bReceive-Job\b': 'rcjb',
            r'\bReceive-PSSession\b': 'rcsn',
            r'\bRemove-ItemProperty\b': 'rp',
            r'\bRemove-Job\b': 'rjb',
            r'\bRemove-Module\b': 'rmo',
            r'\bRemove-PSBreakpoint\b': 'rbp',
            r'\bRemove-PSDrive\b': 'rdr',
            r'\bRemove-PSSession\b': 'rsn',
            r'\bRemove-PSSnapIn\b': 'rsnp',
            r'\bRemove-Variable\b': 'rv',
            r'\bRemove-WMIObject\b': 'rwmi',
            r'\bRename-Item\b': random.choice(['ren', 'rni']),
            r'\bRename-ItemProperty\b': 'rnp',
            r'\bResolve-Path\b': 'rvpa',
            r'\bResume-Job\b': 'rujb',
            r'\bSelect-String\b': 'sls',
            r'\bSet-Alias\b': 'sal',
            r'\bSet-Clipboard\b': 'scb',
            r'\bSet-Item\b': 'si',
            r'\bSet-ItemProperty\b': 'sp',
            r'\bSet-PSBreakpoint\b': 'sbp',
            r'\bSet-TimeZone\b': 'stz',
            r'\bSet-WMIInstance\b': 'swmi',
            r'\bShow-Command\b': 'shcm',
            r'\bSort-Object\b': 'sort',
            r'\bStart-Job\b': 'sajb',
            r'\bStart-Process\b': random.choice(['saps', 'start']),
            r'\bStart-Service\b': 'sasv',
            r'\bStart-Sleep\b': 'sleep',
            r'\bStop-Job\b': 'spjb',
            r'\bStop-Process\b': random.choice(['kill', 'spps']),
            r'\bStop-Service\b': 'spsv',
            r'\bSuspend-Job\b': 'sujb',
            r'\bTee-Object\b': 'tee',
            r'\bTrace-Command\b': 'trcm',
            r'\bWait-Job\b': 'wjb',
            r'\bGet-Help\b': 'help',
            r'\bGet-Variable\b': 'gv',
            r'\bSet-Variable\b': 'sv',

        }


    def transform(self, content: str) -> str:
        if not content.strip():
            return content
            
        content = self._random_space_insertion(content)
        content = self._substitute_aliases(content)
        content = self._random_case_variation(content)
        content = self._reorder_noncritical_blocks(content)
        content = self._random_type_declaration(content)
        return content
        
    def _random_space_insertion(self, text: str) -> str:
        result = []
        in_string = False
        in_curly_var = False  # Track ${} variables
        current_quote = None
        escaped = False
        length = len(text)
        
        i = 0
        while i < length:
            ch = text[i]
            
            # Handle ${} variable boundaries
            if not in_string and not in_curly_var:
                if ch == '$' and i+1 < length and text[i+1] == '{':
                    in_curly_var = True
                    result.append('$')
                    result.append('{')
                    i += 2
                    continue
            
            # Inside ${} variable - no modifications
            if in_curly_var:
                result.append(ch)
                if ch == '}':
                    in_curly_var = False
                i += 1
                continue
            
            # Existing string handling
            if not in_string:
                if ch in ('"', "'"):
                    in_string = True
                    current_quote = ch
            else:
                if escaped:
                    escaped = False
                elif ch == '`' and current_quote == '"':
                    escaped = True
                elif ch == current_quote:
                    in_string = False

            result.append(ch)
            
            # Space insertion logic (only outside strings and ${} vars)
            if not in_string and not in_curly_var:
                if ch in [';', '{', '}', '|', '(', ',']:
                    spaces = random.randint(0, 10)
                    result.append(' ' * spaces)
                    self.stats['spaces_inserted'] += spaces

            i += 1

        return ''.join(result)

    def _substitute_aliases(self, text: str) -> str:
        # Split into string literals and code
        parts = re.split(r'([\'"][^\'"]*[\'"])', text)
        
        for i in range(0, len(parts)):
            # Skip string literals (odd indices)
            if i % 2 == 0:
                for pattern, replacement in self.substitutions.items():
                    if random.random() < 0.7:
                        # Use a lambda to generate random case variations for the alias
                        parts[i] = re.sub(
                            pattern, 
                            lambda m, replacement=replacement: ''.join([
                                c.upper() if random.random() < 0.5 else c.lower() 
                                for c in replacement
                            ]), 
                            parts[i], 
                            flags=re.IGNORECASE
                        )
                        self.stats['aliases_substituted'] += 1
        
        return ''.join(parts)

    def _random_case_variation(self, text: str) -> str:
        keywords = [
            # Core language keywords
            r'\b(function)\b', r'\b(filter)\b', r'\b(param)\b',
            r'\b(begin)\b', r'\b(process)\b', r'\b(end)\b',
            r'\b(if)\b', r'\b(else)\b', r'\b(elseif)\b',
            r'\b(return)\b', r'\b(throw)\b', r'\b(try)\b',
            r'\b(catch)\b', r'\b(finally)\b', r'\b(while)\b',
            r'\b(do)\b', r'\b(until)\b', r'\b(foreach)\b',
            r'\b(switch)\b', r'\b(default)\b', r'\b(break)\b',
            r'\b(continue)\b', r'\b(exit)\b', r'\b(in)\b',
            
            # Advanced function keywords
            r'\b(dynamicparam)\b', r'\b(workflow)\b',
            r'\b(configuration)\b', r'\b(inlinescript)\b',
            
            # Class-related keywords
            r'\b(class)\b', r'\b(enum)\b', r'\b(using)\b',
            
            # Error handling
            r'\b(trap)\b', 
            
            # Flow control
            r'\b(parallel)\b', r'\b(sequence)\b',
            
            # Type keywords
            r'\b(validatecount)\b', r'\b(validatelength)\b',
            r'\b(validatenotnull)\b', r'\b(validatenotempty)\b',
            
            # Common cmdlet verbs (case-insensitive in PS)
            r'\b(get)\b', r'\b(set)\b', r'\b(new)\b',
            r'\b(remove)\b', r'\b(write)\b', r'\b(read)\b',
            r'\b(invoke)\b', r'\b(test)\b', r'\b(import)\b',
            r'\b(export)\b', r'\b(select)\b', r'\b(where)\b',
            r'\b(foreach-object)\b', r'\b(where-object)\b',
            
            # Special variables
            r'\b(\$args)\b', r'\b(\$this)\b', r'\b(\$input)\b',
            r'\b(\$null)\b', r'\b(\$true)\b', r'\b(\$false)\b',
            
            # Operators
            r'\b(-eq)\b', r'\b(-ne)\b', r'\b(-gt)\b',
            r'\b(-ge)\b', r'\b(-lt)\b', r'\b(-le)\b',
            r'\b(-like)\b', r'\b(-match)\b', r'\b(-contains)\b',
            r'\b(-replace)\b', r'\b(-and)\b', r'\b(-or)\b',
            r'\b(-not)\b', r'\b(-is)\b', r'\b(-as)\b',
            
            # Special methods
            r'\b(ToString)\b', r'\b(GetType)\b', r'\b(Equals)\b',
            
            # Common parameters
            r'\b(-ErrorAction)\b', r'\b(-WarningAction)\b',
            r'\b(-InformationAction)\b', r'\b(-Verbose)\b',
            r'\b(-Debug)\b', r'\b(-WhatIf)\b', r'\b(-Confirm)\b'
        ]

        for keyword in keywords:
            matches = list(re.finditer(keyword, text, re.IGNORECASE))
            for match in reversed(matches):
                if random.random() < 0.5:  # Increased chance of variation
                    original = match.group()
                    # Preserve special characters in patterns like $args
                    if original.startswith('$'):
                        varied = original[0] + ''.join(
                            c.upper() if random.random() < 0.5 else c.lower()
                            for c in original[1:]
                        )
                    else:
                        varied = ''.join(
                            c.upper() if random.random() < 0.5 else c.lower()
                            for c in original
                        )
                    
                    # Preserve operator dashes
                    if keyword.startswith(r'\-'):
                        varied = '-' + varied[1:].replace('-', '')
                    
                    text = f"{text[:match.start()]}{varied}{text[match.end():]}"
                    self.stats['case_variations'] += 1

        return text
        
    def _random_type_declaration(self, text: str) -> str:
        parts = re.split(r'([\'"][^\'"]*[\'"])', text)
        
        for i in range(len(parts)):
            if i % 2 == 0:
                parts[i] = re.sub(
                    r'\[\s*([\w.]+)\s*\]',
                    lambda m: (
                        f'[{" " * random.randint(0,1)}'
                        f'{"".join([c.upper() if random.random() < 0.5 else c.lower() for c in m.group(1)])}'
                        f'{" " * random.randint(0,1)}]'
                    ),
                    parts[i]
                )
        return ''.join(parts)

    def _reorder_noncritical_blocks(self, text: str) -> str:
        blocks = text.split('\n\n')
        
        for i in range(len(blocks)):
            lines = blocks[i].splitlines()
            if all(line.strip().startswith('#') for line in lines if line.strip()):
                random.shuffle(lines)
                blocks[i] = "\n".join(lines)
        
        return '\n\n'.join(blocks)

    def get_stats(self) -> Dict[str, Any]:
        return self.stats