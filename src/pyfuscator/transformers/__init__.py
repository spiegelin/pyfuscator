"""
Transformers for code obfuscation.
"""
# Import from Python transformers
from pyfuscator.transformers.python import (
    ImportTracker, ObfuscateImports, ReplaceImportNames,
    RenameIdentifiers, ImportRenamer, EncryptStrings,
    DynamicFunctionBody, InsertJunkCode
)

# Import from PowerShell transformers
from pyfuscator.transformers.powershell import (
    RenameIdentifiers as PSRenameIdentifiers,
    ObfuscateStrings, CommandTokenizer,
    InsertJunkCode as PSInsertJunkCode, UseDotNetMethods,
    SecureStringTransformer,
    RemoveComments, LowerEntropy, Base64Encoder, PowerShellObfuscator
)

__all__ = [
    # Python transformers
    'ImportTracker',
    'ObfuscateImports',
    'ReplaceImportNames',
    'RenameIdentifiers',
    'ImportRenamer',
    'EncryptStrings',
    'DynamicFunctionBody',
    'InsertJunkCode',
    
    # PowerShell transformers
    'PSRenameIdentifiers',
    'ObfuscateStrings',
    'CommandTokenizer',
    'PSInsertJunkCode',
    'UseDotNetMethods',
    'SecureStringTransformer',
    'RemoveComments',
    'LowerEntropy',
    'Base64Encoder',
    'PowerShellObfuscator',
]
