# PyFuscator

A powerful code obfuscation tool that transforms your source code into a difficult-to-understand form while preserving its full functionality.

## Overview

PyFuscator is designed for security professionals, Red Teamers, and penetration testers who need to bypass detection mechanisms and protect their operational code. The tool supports multiple programming languages and applies common obfuscation techniques to evade security controls while maintaining full code functionality.

## Security Professional Use Cases

- **Red Team Operations** - Obfuscate payload delivery mechanisms to bypass detection
- **Penetration Testing** - Modify security testing scripts to avoid triggering defensive measures
- **Command & Control** - Disguise C2 communications and operational scripts
- **OPSEC Enhancement** - Protect operational security by making code analysis more difficult
- **AV/EDR Evasion** - Modify script signatures to bypass antivirus and endpoint detection
- **Custom Implant Development** - Create hard-to-analyze persistence mechanisms

## Features

### Python Obfuscation

- **String Encryption** - Encrypts string literals with base64 encoding
- **Variable Renaming** - Transforms variable, function, and class names into meaningless random strings
- **Import Obfuscation** - Hides and manipulates import statements
- **Junk Code Insertion** - Adds random non-functional code
- **Dynamic Function Execution** - Wraps function bodies with dynamic execution to hide logic
- **Comment Removal** - Strips all comments and docstrings from the code

### PowerShell Obfuscation

- **String Obfuscation** - Encrypts string literals with various techniques
- **Identifier Renaming** - Transforms variable and function names into random strings
- **Command Tokenization** - Breaks PowerShell commands into obfuscated tokens
- **Junk Code Insertion** - Adds random non-functional code
- **.NET Method Obfuscation** - Uses .NET methods to obfuscate operations
- **SecureString Obfuscation** - Leverages PowerShell SecureString for added security
- **ADS Storage** - Hides scripts in Alternate Data Streams
- **Comment Removal** - Strips all comments from the code

## Installation

```bash
# Install from PyPI
pip install pyfuscator

# Or install from source
git clone https://github.com/user/pyfuscator.git
cd pyfuscator
pip install .
```

## Usage

PyFuscator provides language-specific commands to handle different obfuscation techniques:

### Basic Usage

```bash
# Python obfuscation
pyfuscator python input.py output.py

# PowerShell obfuscation
pyfuscator powershell input.ps1 output.ps1
```

### Python-Specific Obfuscation

```bash
pyfuscator python [OPTIONS] INPUT_FILE OUTPUT_FILE
```

Options:

| Option | Description |
|--------|-------------|
| `-r, --remove-comments` | Remove comments from the code (enabled by default) |
| `-j, --junk-code N` | Insert N random junk statements |
| `-o, --obfuscate-imports` | Obfuscate import statements and their references |
| `-i, --identifier-rename` | Rename variables, functions and class names |
| `-d, --dynamic-exec` | Wrap function bodies with dynamic execution |
| `-s, --encrypt-strings` | Encrypt string literals with base64 encoding |
| `-e, --encrypt N` | Apply N layers of encryption (0-5) |
| `-a, --all` | Apply all obfuscation techniques except encryption |
| `-v, --verbose` | Show detailed logs and statistics during obfuscation |

### PowerShell-Specific Obfuscation

```bash
pyfuscator powershell [OPTIONS] INPUT_FILE OUTPUT_FILE
```

Options:

| Option | Description |
|--------|-------------|
| `-r, --remove-comments` | Remove comments from the code (enabled by default) |
| `-j, --junk-code N` | Insert N random junk statements |
| `-c, --tokenize-commands` | Tokenize and obfuscate PowerShell commands |
| `-i, --identifier-rename` | Rename variables and functions |
| `-d, --dotnet-methods` | Use .NET methods for obfuscation |
| `-s, --secure-strings` | Use SecureString for string obfuscation |
| `-e, --encrypt N` | Apply N layers of encoding (0-5) |
| `-a, --ads` | Store scripts in Alternate Data Streams (Windows only) |
| `--all` | Apply all PowerShell obfuscation techniques |
| `-v, --verbose` | Show detailed logs and statistics during obfuscation |


## Example Transformations

### Python Example

Original code:
```python
import numpy as np

def calculate_sum(a, b):
    """Add two numbers and return the result."""
    return a + b

result = calculate_sum(10, 20)
print("The result is:", result)
```

Obfuscated code (with all techniques, except encryption):
```python

if False:
    oOxKjDI4 = 91
if False:
    uu2l8rv2 = 69
XKcjzGSc = __import__(__import__(__import__('base64').b64decode('YmFzZTY0').decode()).b64decode(__import__('base64').b64decode('Ym5WdGNIaz0=').decode()).decode(__import__('base64').b64decode('dXRmLTg=').decode()))

def t25nFf8z(b6WJkQlT, TNe39vUg):
    if (1 > 100):
        'This code will never execute'

    def rioand():
        return (b6WJkQlT + TNe39vUg)
    pebpvz = rioand()
    return pebpvz
dmAHLkYI = t25nFf8z(10, 20)
print(__import__('base64').b64decode('VGhlIHJlc3VsdCBpczo=').decode(), dmAHLkYI)
ZDYS0AJO = __import__('base64').b64decode('bE12NzE=').decode()
try:
    sq5aKGpR = True
except Exception:
    sq5aKGpR = False
fPISuYlv = (__import__('base64').b64decode('bk9vcw==').decode() + __import__('base64').b64decode('ZnQ0Uw==').decode())
```

### PowerShell Example

Original code:
```powershell
function Get-Hello {
    param(
        [string]$Name = "World"
    )
    # Return a greeting
    return "Hello, $Name!"
}

Get-Hello
```

Obfuscated code (with all techniques):
```powershell
function DafpOwV0 { 
    param(
        [Parameter(Mandatory=$false)]
        [string]$eEy82 = [char[]](87)-join''+"o"+"r"+"l"+"d"
    )
    
    (& { 
        $data = [System.Convert]::FromBase64String('SABlAGwAbABvACwAIAAkAGUARQB5ADgAMgAhAA=='); 
        $ms = New-Object System.IO.MemoryStream; 
        $ms.Write($data, 0, $data.Length); 
        $ms.Seek(0,0) | Out-Null; 
        $sr = New-Object System.IO.StreamReader($ms, [System.Text.Encoding]::Unicode); 
        $decoded = $sr.ReadToEnd(); 
        Invoke-Expression $decoded
    })
}

# Junk code
$jMip4 = 'BxAjc4Tg'
$Cd9bR = @{ Q7M40 = 13; iYZkq = 'mG5uujDX'; puhpL = $false; t7OkX = 'mG5uujDX' }
if ($r08HF -le 67) { $asfoo = $true }

# Tokenized and obfuscated command invocation
(& {$p0='Inv';$p1='oke-';$p2='Expr';$p3='essi';$p4='on';$p0+$p1+$p2+$p3+$p4}) "DafpOwV0"
```

## How It Works

PyFuscator applies a series of transformations to your code:

1. **Comment Removal**: Strips all comments and docstrings from the code.
2. **Junk Code Insertion**: Adds random, non-functional code to obscure the original logic.
3. **Import Obfuscation** (Python) / **Command Tokenization** (PowerShell): Hides and manipulates import statements or command names.
4. **Identifier Renaming**: Changes all variable, function, and class names to random strings.
5. **String Encryption**: Encrypts string literals using various techniques.
6. **Dynamic Function Execution** (Python) / **.NET Method Obfuscation** (PowerShell): Wraps function bodies or operations with obfuscated execution methods.
7. **Lower Entropy** (PowerShell): Reduces the entropy of the script by adding random spacing, command substitution with aliases, and reordering non-critical parts.
8. **ADS Storage** (PowerShell, Windows only): Stores the script in Alternate Data Streams for additional stealth.
9. **Layer Encryption**: Applies multiple layers of encryption to the entire script (if specified).

## Important Notes

1. The obfuscated code will run slower than the original due to the added complexity
2. Obfuscated code looks suspicious
3. Comment removal is applied by default but can also be explicitly specified with `-r`
4. Excessive encryption layers can significantly increase code size and runtime

## Security Considerations

PyFuscator provides a layer of protection against static analysis, signature-based detection, and reverse engineering attempts. However, it's important to understand that:

- Obfuscation is not encryption - a determined analyst may still be able to recover the original logic
- The tool is designed to make reverse engineering difficult, not impossible
- For maximum security, combine code obfuscation with other evasion mechanisms
- Always use this tool in accordance with proper authorization and legal compliance

## Use Cases

- **Evasion Testing** - Evaluate security product effectiveness against obfuscated malicious code
- **Red Team Campaigns** - Protect custom tooling during adversary emulation exercises
- **Security Research** - Study obfuscation techniques and develop improved detection methods
- **Tool Protection** - Prevent unauthorized analysis of proprietary security tools
- **Tradecraft Development** - Research and enhance code protection techniques

## Ethical Usage

This tool is intended for legitimate security professionals conducting authorized testing activities. The authors do not endorse or support illegal or unauthorized use. Always:

1. Ensure proper authorization before deploying obfuscated code
2. Follow responsible disclosure practices
3. Comply with all applicable laws and regulations
4. Use this tool as part of a comprehensive security program

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.