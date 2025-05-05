"""
Core functionality for PyFuscator.
"""
# Removing import of Obfuscator to avoid circular imports
# Import utility functions only
from pyfuscator.core.utils import (
    random_name, 
    encode_string, 
    wrap_with_exec, 
    validate_python_code,
    generate_random_statement,
    remove_comments,
    fix_slice_syntax,
    set_parent_nodes
)

# Import global variables
from pyfuscator.core.globals import IMPORT_ALIASES, IMPORT_MAPPING

# Import base transformer class
from pyfuscator.core.transformer import Transformer

# Import encryption methods
from pyfuscator.core.methods import (
    encryption_method_1,
    encryption_method_2,
    encryption_method_3,
    encryption_method_4,
    encryption_method_5,
    generate_prime_number,
    mod_exp,
    extended_gcd
)

__all__ = [
    # 'Obfuscator', # Removed to prevent circular imports
    # 'obfuscate_file', # Removed to prevent circular imports
    'random_name',
    'encode_string',
    'wrap_with_exec',
    'validate_python_code',
    'generate_random_statement',
    'remove_comments',
    'fix_slice_syntax',
    'set_parent_nodes',
    'IMPORT_ALIASES',
    'IMPORT_MAPPING',
    'Transformer',
    # Encryption methods
    'encryption_method_1',
    'encryption_method_2',
    'encryption_method_3',
    'encryption_method_4',
    'encryption_method_5',
    'generate_prime_number',
    'mod_exp',
    'extended_gcd'
]
