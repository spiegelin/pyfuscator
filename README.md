# pyfuscator

## Project Overview

`pyfuscator.py` is a Python-based tool designed to obfuscate code written in various scripting languages. It utilizes multiple techniques to transform code into a form that is more difficult to understand and reverse engineer. These techniques are ideal for protecting sensitive logic, intellectual property, or code that needs to be obscured for security reasons.

The tool supports various obfuscation methods, including:
- Blob/Rabbit Holes
- Identifier Renaming (Name Mangling)
- Removing Comments and Formatting
- String Encryption/Encoding
- Dynamic Code Execution
- Manual Control Flow Rewriting

The obfuscation process generates a "hard-to-read" version of your source code while maintaining its original functionality. The obfuscated code is output to a new file, which you can then use to distribute or protect your logic.

## Usage

The tool is executed via the command line and takes two arguments:

```
python obusfactor.py <file-to-obfuscate> <result>
```

Where:
- `<file-to-obfuscate>` is the path to the source code file you want to obfuscate.
- `<result>` is the path to the file where the obfuscated code will be saved.

### Example:
```
python obusfactor.py example_script.py obfuscated_script.py
```

## Features & Techniques

### 1. **Blob/Rabbit Holes**
The code is obfuscated by introducing "rabbit holes"—confusing and unnecessary segments of code designed to mislead anyone trying to reverse-engineer it. This technique makes it harder for the attacker to find the core functionality of the program by adding layers of confusion.

### 2. **Identifier Renaming (Name Mangling)**
All function, variable, and class names are automatically renamed to meaningless strings (e.g., turning `calculate_sum` into `a1b2c3`). This makes it difficult to understand the code’s structure and logic.

### 3. **Removing Comments and Formatting**
All comments, docstrings, and extra whitespace are removed to reduce the clarity of the code. Without meaningful comments or explanations, the code becomes more difficult to follow and reverse-engineer.

### 4. **String Encryption/Encoding**
Strings in the code, including hardcoded values such as passwords or key phrases, are encrypted or encoded. For instance, strings might be encoded in Base64 and then dynamically decoded at runtime. This technique ensures that sensitive information isn’t visible in the clear within the source code.

### 5. **Dynamic Code Execution**
Certain parts of the code are obfuscated and encoded so that they can only be decoded and executed dynamically at runtime. This can involve using Python's `exec()` function or other dynamic execution methods to delay the understanding of critical code parts until runtime.

### 6. **Manual Control Flow Rewriting**
The logical flow of the program is altered by refactoring loops and conditionals, making the structure of the code less intuitive. Redundant or "dummy" code is inserted that does not affect the final output, but increases the complexity and difficulty of analysis.

## Installation

To use `obusfactor.py`, you need Python 3.x installed on your system. You can check if Python is installed by running the following command in your terminal:

```
python --version
```

If Python is not installed, please download and install it from [python.org](https://www.python.org/downloads/).

### Dependencies

`obusfactor.py` requires the following Python libraries:
- `base64` for string encoding and decoding
- `random` and `string` for generating random names and strings
- `exec` function for dynamic execution

These libraries are included with Python by default, so no additional installations are necessary.

## Example Workflow

1. **Prepare the Script to Obfuscate:**
   Place the script you want to obfuscate in a folder on your machine.

2. **Run the Obfuscation Tool:**
   Run the tool with the following command:

   ```
   python obusfactor.py your_script.py obfuscated_script.py
   ```

3. **Obfuscated Code Output:**
   The tool will generate an obfuscated version of your script in the `obfuscated_script.py` file. This file will be difficult to read or reverse-engineer, but it will still perform the same operations as the original.

4. **Review and Distribute:**
   You can now safely distribute the obfuscated code knowing that it is much harder for anyone to reverse-engineer or understand the logic.

## Example

### Input Code (`example_script.py`):

```python
# This is a simple example script

def calculate_sum(a, b):
    return a + b

result = calculate_sum(10, 20)
print("The result is:", result)
```

### Output Code (`obfuscated_script.py`):

```python
exec('a1b2c3="calc";d4e5f6="su";g7h8i9="m";j0k1l2="r";m3n4o5="s";p6q7r8=eval(chr(98)+chr(97)+chr(115)+chr(101)+chr(54)+chr(99)+chr(105)+chr(108)+chr(107)))')
```

This is a very simplified example. The obfuscated code in the output will look like a series of meaningless names and encoded strings, making it difficult to reverse-engineer.

## Contributing

We welcome contributions to improve the tool! If you have any ideas for new obfuscation techniques or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Thank you for using `obusfactor.py`—your simple solution for complex code obfuscation!