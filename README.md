# PyFuscator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6%2B-blue" alt="Python 3.6+"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Status: Active"/>
</p>

```
             __                  _           
  _ __ _  _ / _|_  _ ___ __ __ _| |_ ___ _ _ 
 | '_ \ || |  _| || (_-</ _/ _` |  _/ _ \ '_|
 | .__/\_, |_|  \_,_/__/\__\__,_|\__\___/_|  
 |_|   |__/                                  
```

**PyFuscator** is an advanced Python code obfuscation tool designed to transform your code into a form that is extremely difficult to understand and reverse engineer while preserving its original functionality.

## 🔒 Features

PyFuscator provides multiple layers of obfuscation through a combination of techniques:

- **🔄 Identifier Renaming** - Transforms variable, function, and class names into meaningless random strings
- **📦 Import Obfuscation** - Disguises import statements and their references throughout the code
- **🔡 String Encryption** - Encrypts string literals with base64 encoding and dynamic decryption
- **📃 Junk Code Insertion** - Adds randomly generated, syntactically valid but unreachable code
- **⚙️ Dynamic Function Execution** - Wraps function bodies with dynamic execution to hide logic
- **⛓️ Multi-layer Encryption** - Applies multiple layers of encryption with various algorithms
- **✂️ Comment Removal** - Strips away comments and formatting to reduce clarity

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/spiegelin/PyFuscator.git
cd PyFuscator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📋 Usage

Basic usage:
```bash
python python-obfuscator.py [options] input_file output_file
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-e NUM, --encrypt NUM` | Apply NUM layers of encryption |
| `-j NUM, --junk-code NUM` | Insert NUM random junk statements |
| `-r, --remove-comments` | Remove comments from the original code |
| `-o, --obfuscate-imports` | Obfuscate import statements and their references |
| `-i, --identifier-rename` | Rename variables, functions and class names |
| `-d, --dynamic-exec` | Wrap function bodies with dynamic execution |
| `-a, --all` | Apply all obfuscation techniques except encryption |
| `-v, --verbose` | Log every step of the obfuscation process |

### Example Commands

Basic obfuscation with identifier renaming and 2 encryption layers:
```bash
python python-obfuscator.py -i -e 2 input.py output.py
```

Maximum obfuscation with all features enabled:
```bash
python python-obfuscator.py -i -e 3 -j 300 -r -o -d input.py output.py
```

Only identifier renaming:
```bash
python python-obfuscator.py -i input.py output.py
```

Only add junk code:
```bash
python python-obfuscator.py -j 150 input.py output.py
```

Apply all techniques with verbose logging:
```bash
python python-obfuscator.py -a -e 2 -v input.py output.py
```

## 🛡️ Obfuscation Process

1. **Comment Removal**: Strips all comments while maintaining code structure
2. **Junk Code Injection**: Inserts randomized, syntactically valid code at the beginning and end
3. **Import Obfuscation**: Transforms import statements into dynamic base64-encoded imports
4. **Identifier Renaming**: Changes all variable, function and class names to random strings
5. **String Encryption**: Encrypts string literals with base64 encoding
6. **Dynamic Function Execution**: Wraps function bodies with opaque execution wrappers
7. **Multi-layer Encryption**: Applies multiple layers of encryption algorithms

## 📝 Example Transformation

### Original Code:
```python
import numpy as np

def calculate_sum(a, b):
    """Add two numbers and return the result."""
    return a + b

result = calculate_sum(10, 20)
print("The result is:", result)
```

### Obfuscated Code:
```python
# Junk code (beginning)
fVusrDIK = 992
pass
Mh3F2dnk = 860
pass

# Import obfuscation
NmEOKslC = __import__(__import__('base64').b64decode('bnVtcHk=').decode('utf-8'))

# Function with identifier renaming + dynamic execution
def XOl2HEM3(i7RvB, FboMb):
    # Dummy unreachable condition
    if (15 < 4):
        print('junk')
    # Dynamic function body execution
    def KX4uhj():
        return (i7RvB + FboMb)
    result = KX4uhj()
    return result

# Renamed identifiers + encrypted string
otVN82l6 = XOl2HEM3(10, 20)
print(__import__('base64').b64decode('VGhlIHJlc3VsdCBpczo=').decode('utf-8'), otVN82l6)

# Junk code (end)
ywEpfHsv = [45, 23, 91]
if ((44 % 2) == 1):
    cwrOaraT = 90
```

## ⚠️ Important Notes

1. The obfuscated code will run slower than the original due to the added complexity
2. Some code analysis tools may flag obfuscated code as suspicious
3. At least one obfuscation method must be selected when running the tool
4. Excessive encryption layers can significantly increase code size and runtime

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📧 Contact

If you have any questions or feedback, please open an issue on GitHub.

---

⭐ If you find this project useful, please star it on GitHub!