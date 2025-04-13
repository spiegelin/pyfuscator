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
    ObfuscateStrings, EncodeCommands, CommandTokenizer,
    InsertJunkCode as PSInsertJunkCode, UseDotNetMethods,
    SecureStringTransformer, AlternateDataStreams,
    RemoveComments, LowerEntropy, Base64Encoder,
    PowerShellScriptEncryptor, PowerShellObfuscator
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
    'EncodeCommands',
    'CommandTokenizer',
    'PSInsertJunkCode',
    'UseDotNetMethods',
    'SecureStringTransformer',
    'AlternateDataStreams',
    'RemoveComments',
    'LowerEntropy',
    'Base64Encoder',
    'PowerShellScriptEncryptor',
    'PowerShellObfuscator',
]
