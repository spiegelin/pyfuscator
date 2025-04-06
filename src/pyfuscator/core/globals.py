"""
Shared global variables for the pyfuscator package.

This module contains global variables that are shared between different
modules to prevent circular imports.
"""
from typing import Dict, Set

# Global mappings for import-aware obfuscation
# These are used by both imports.py and obfuscator.py
IMPORT_ALIASES: Set[str] = set()
IMPORT_MAPPING: Dict[str, str] = {} 