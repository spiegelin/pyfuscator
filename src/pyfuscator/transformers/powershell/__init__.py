"""
PowerShell-specific obfuscation transformers.
"""
from pyfuscator.transformers.powershell.identifiers import RenameIdentifiers
from pyfuscator.transformers.powershell.strings import ObfuscateStrings
from pyfuscator.transformers.powershell.encoding import EncodeCommands
from pyfuscator.transformers.powershell.concat import CommandTokenizer
from pyfuscator.transformers.powershell.junk import InsertJunkCode
from pyfuscator.transformers.powershell.securestring import SecureStringTransformer
from pyfuscator.transformers.powershell.dotnet import UseDotNetMethods
from pyfuscator.transformers.powershell.ads import AlternateDataStreams
from pyfuscator.transformers.powershell.remove_comments import RemoveComments
from pyfuscator.transformers.powershell.lower_entropy import LowerEntropy
from pyfuscator.transformers.powershell.base64 import Base64Encoder
from pyfuscator.transformers.powershell.script_encryptor import PowerShellScriptEncryptor
from pyfuscator.transformers.powershell.coordinator import PowerShellObfuscator

__all__ = [
    'RenameIdentifiers',
    'ObfuscateStrings',
    'EncodeCommands',
    'CommandTokenizer',
    'InsertJunkCode',
    'UseDotNetMethods',
    'SecureStringTransformer',
    'AlternateDataStreams',
    'RemoveComments',
    'LowerEntropy',
    'Base64Encoder',
    'PowerShellScriptEncryptor',
    'PowerShellObfuscator'
] 