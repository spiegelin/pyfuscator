#!/usr/bin/env python3
import ast
import astunparse
import base64
import io
import random
import re
import string
import sys
import tokenize
import argparse

from colorama import Fore, Style, init
init(autoreset=True)

# Global sets/dictionaries for import obfuscation.
IMPORT_ALIASES = set()
IMPORT_MAPPING = {}  # Maps original import names (or original alias) to new random alias.

# Banner for the help menu - add color codes
BANNER = fr'''{Fore.CYAN}
             __                  _           
  _ __ _  _ / _|_  _ ___ __ __ _| |_ ___ _ _ 
 | '_ \ || |  _| || (_-</ _/ _` |  _/ _ \ '_|
 | .__/\_, |_|  \_,_/__/\__\__,_|\__\___/_|  
 |_|   |__/                                  
{Style.RESET_ALL}'''

# --- Helper functions ---

def random_name(length=8):
    """
    Generate a random variable name that's a valid Python identifier.
    Ensures it's not a Python keyword and starts with a letter.
    """
    # List of Python keywords to avoid
    python_keywords = [
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
        'with', 'yield'
    ]
    
    # Ensure the first character is a letter
    first = random.choice(string.ascii_letters)
    
    # Generate the rest of the name with letters and digits
    if length > 1:
        rest = ''.join(random.choices(string.ascii_letters + string.digits, k=length-1))
        name = first + rest
    else:
        name = first
    
    # Check if it's a Python keyword and regenerate if it is
    if name in python_keywords:
        return random_name(length)  # Recursive call to try again
    
    return name

def encode_string(s):
    """Encode a string to base64 and create a decode expression."""
    encoded = base64.b64encode(s.encode('utf-8')).decode('utf-8')
    return f"__import__('base64').b64decode('{encoded}').decode('utf-8')"

def wrap_with_exec(code_str):
    b64_code = base64.b64encode(code_str.encode('utf-8')).decode('utf-8')
    # Always use exec since we're executing statements, not evaluating expressions
    return f"exec(__import__('base64').b64decode('{b64_code}').decode('utf-8'), globals(), locals())"

def validate_python_code(code_str):
    """Validate if the provided string is valid Python code."""
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def generate_random_statement():
    """Generate a random Python statement that follows PEP 8 style guidelines."""
    # Decide on a statement type with weights favoring simpler constructs
    type_weights = [
        ("assignment", 0.3),
        ("loop", 0.15),
        ("conditional", 0.15),
        ("function_def", 0.15),
        ("simple_expression", 0.15),
        ("class_def", 0.05),
        ("try_except", 0.05)
    ]
    statement_types, weights = zip(*type_weights)
    statement_type = random.choices(statement_types, weights=weights, k=1)[0]
    
    # Maximum number of attempts to generate valid code
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            if statement_type == "assignment":
                var_name = random_name()
                # Simple assignments are safest
                value_type = random.choice(["int", "str", "list", "dict"])
                
                if value_type == "int":
                    value = str(random.randint(0, 1000))
                elif value_type == "str":
                    value = f"'{random_name(5)}'"
                elif value_type == "list":
                    items = []
                    for _ in range(random.randint(1, 3)):
                        items.append(str(random.randint(1, 100)))
                    value = f"[{', '.join(items)}]"
                elif value_type == "dict":
                    items = []
                    for _ in range(random.randint(1, 2)):
                        key = random_name(3)
                        items.append(f"'{key}': {random.randint(1, 100)}")
                    value = f"{{{', '.join(items)}}}"
                
                code = f"{var_name} = {value}"
                
            elif statement_type == "loop":
                var_name = random_name()
                inner_var = random_name()
                # Simple for loop with a safe range
                loop_count = random.randint(3, 10)
                body = f"{inner_var} = {var_name}"
                code = f"for {var_name} in range({loop_count}):\n    {body}"
                
            elif statement_type == "conditional":
                var_name = random_name()
                # Simple if statement with a boolean condition
                condition = random.choice([
                    "True",
                    "False",
                    f"{random.randint(1, 10)} > {random.randint(1, 10)}"
                ])
                body = f"{var_name} = {random.randint(1, 100)}"
                code = f"if {condition}:\n    {body}"
                
            elif statement_type == "function_def":
                func_name = random_name()
                # Simple function with no parameters
                body = f"    return {random.randint(1, 100)}"
                code = f"def {func_name}():\n{body}"
                
            elif statement_type == "simple_expression":
                var_name = random_name()
                # Very simple expressions that are unlikely to cause issues
                expr = random.choice([
                    f"{random.randint(1, 100)} + {random.randint(1, 100)}",
                    f"'{random_name(4)}' + '{random_name(4)}'",
                    f"len('{random_name(5)}')",
                    f"bool({random.choice(['True', 'False', '0', '1'])})"
                ])
                code = f"{var_name} = {expr}"
                
            elif statement_type == "class_def":
                class_name = ''.join(word.capitalize() for word in random_name().split('_'))
                # Very simple class with just an init method
                code = f"class {class_name}:\n    def __init__(self):\n        pass"
                
            elif statement_type == "try_except":
                var_name = random_name()
                # Simple try-except with a safe operation
                code = f"try:\n    {var_name} = True\nexcept Exception:\n    {var_name} = False"
            
            else:
                # Default safe assignment
                var_name = random_name()
                code = f"{var_name} = None"
            
            # Validate the generated code
            if validate_python_code(code):
                return code
            
        except Exception:
            # If any exception occurs, continue to the next attempt
            continue
    
    # If all attempts failed, return a very safe statement
    return f"{random_name()} = None"

def generate_random_blob_code(num_statements=50):
    """Generate valid Python code following PEP 8 style guidelines."""
    valid_statements = []
    attempts = 0
    max_attempts = num_statements * 2  # Allow twice as many attempts as requested statements
    
    # Generate statements and validate each one
    while len(valid_statements) < num_statements and attempts < max_attempts:
        statement = generate_random_statement()
        attempts += 1
        
        # Skip empty statements
        if not statement.strip():
            continue
            
        try:
            # Try to parse the statement to verify it's valid
            ast.parse(statement)
            
            # Add a newline after statements with indentation (like if, for, etc.)
            if statement.strip().endswith(':'):
                statement += '\n    pass'
                
            valid_statements.append(statement)
        except SyntaxError:
            # Skip invalid statements
            continue
    
    # Join the statements with proper spacing according to PEP 8
    # - Two blank lines between top-level functions and classes
    # - One blank line between methods in a class
    formatted_code = []
    prev_was_class_or_func = False
    
    for stmt in valid_statements:
        # If the previous statement was a class or function definition and this one is too,
        # add two blank lines in between
        is_class_or_func = stmt.lstrip().startswith(('def ', 'class '))
        
        if prev_was_class_or_func and is_class_or_func:
            formatted_code.append("\n\n")
        elif formatted_code:  # Add one blank line between all other statements
            formatted_code.append("\n")
            
        formatted_code.append(stmt)
        prev_was_class_or_func = is_class_or_func
    
    return ''.join(formatted_code)

def remove_comments(source):
    """
    Remove comments from Python source code while preserving function structure.
    This is a simpler approach that uses regex to remove only # comments.
    """
    import re
    
    # Only remove # comments, not docstrings
    # This is safer to prevent indentation errors
    lines = source.split('\n')
    result = []
    
    for line in lines:
        # Remove comments that start with #
        comment_pos = line.find('#')
        if comment_pos >= 0:
            # Make sure the # is not inside a string
            in_string = False
            string_char = None
            escaped = False
            
            for i, char in enumerate(line[:comment_pos]):
                if escaped:
                    escaped = False
                    continue
                
                if char == '\\':
                    escaped = True
                    continue
                
                if not in_string and char in ['"', "'"]:
                    in_string = True
                    string_char = char
                elif in_string and char == string_char:
                    in_string = False
            
            if not in_string:
                line = line[:comment_pos]
        
        result.append(line)
    
    return '\n'.join(result)

def fix_slice_syntax(code):
    """
    Fixes extra outer parentheses around slice expressions in subscript operations.
    Example: converts
        mVUIiImo[(a:(a + b)*4, c:(c + d))]
    to
        mVUIiImo[a:(a + b)*4, c:(c + d)]
    """
    pattern = re.compile(r'(\[)\(\s*(.*?)\s*\)(\])', re.DOTALL)
    fixed_code = pattern.sub(r'\1\2\3', code)
    return fixed_code

# --- Encryption functions from ofuscator.py ---

def generate_prime_number():
    """Generate a random prime number."""
    def check_if_it_is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    while True:
        num = random.randint(1000, 1000000)
        if check_if_it_is_prime(num):
            return num

def mod_exp(base, exp, mod):
    """Modular exponentiation: (base^exp) % mod."""
    result = 1
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp //= 2
    return result

def extended_gcd(a, b):
    """Extended Euclidean algorithm to find modular inverse."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_s % b

def encryption_method_1(code_to_encode):
    """Encryption method 1: Linear congruential encryption."""
    prime_number = generate_prime_number()
    salt = random.randint(1, 300)
    
    # Encrypt
    message_int = []
    for b in code_to_encode:
        message_int.append(ord(b))
    ct = []
    for number in message_int:
        ct.append((prime_number * number + salt) % 256)
    encrypted_message = ''.join([hex(i)[2:].zfill(2) for i in ct])
    decryption_func_name = random_name()

    # Generate output
    output_content = ""
    output_content += f"def {decryption_func_name}(prime_number, crypted_msg, salt):\n"
    output_content += "    encryptedlist = [int(crypted_msg[i:i+2], 16) for i in range(0, len(crypted_msg), 2)]\n"
    output_content += "    table = {((prime_number * char + salt) % 256): char for char in range(256)}\n"
    output_content += "    recovery2 = [table.get(num) for num in encryptedlist]\n"
    output_content += "    return bytes(recovery2)\n\n"
    output_content += f"_crypted_code = \"{encrypted_message}\"\n"
    output_content += f"_salt = {salt}\n"
    output_content += f"_prime_number = {prime_number}\n"
    output_content += f"_decrypted_code = {decryption_func_name}(_prime_number, _crypted_code, _salt).decode('utf-8')\n"
    output_content += "exec(_decrypted_code)\n"
    
    return output_content

def encryption_method_2(code_to_encode):
    """Encryption method 2: XOR with shuffled key."""
    salt = random.randint(50, 500)
    key = random.randint(10, 250)
    shuffle_key = list(range(256))
    random.shuffle(shuffle_key)
    reverse_key = {v: k for k, v in enumerate(shuffle_key)}
    
    encoded_bytes = bytearray()
    for char in code_to_encode.encode():
        transformed = (shuffle_key[(char ^ key) % 256] + salt) % 256
        encoded_bytes.append(transformed)
    
    encrypted_message = ''.join([hex(i)[2:].zfill(2) for i in encoded_bytes])
    decryption_func_name = random_name()
    
    output_content = ""
    output_content += f"def {decryption_func_name}(encrypted_message, key, salt, reverse_key):\n"
    output_content += "    encrypted_bytes = [int(encrypted_message[i:i+2], 16) for i in range(0, len(encrypted_message), 2)]\n"
    output_content += "    decrypted_bytes = bytearray(reverse_key[(b - salt) % 256] ^ key for b in encrypted_bytes)\n"
    output_content += "    return decrypted_bytes.decode('utf-8')\n\n"
    
    output_content += f"_crypted_code = \"{encrypted_message}\"\n"
    output_content += f"_key = {key}\n"
    output_content += f"_salt = {salt}\n"
    output_content += f"_reverse_key = {reverse_key}\n"
    output_content += f"_decrypted_code = {decryption_func_name}(_crypted_code, _key, _salt, _reverse_key)\n"
    output_content += "exec(_decrypted_code)\n"
    
    return output_content

def encryption_method_3(code):
    """Encryption method 3: RSA-like encryption."""
    prime1 = generate_prime_number()
    prime2 = generate_prime_number()
    n = prime1 * prime2
    phi = (prime1 - 1) * (prime2 - 1)
    e = 65537
    d = extended_gcd(e, phi)
    
    encrypted_values = [mod_exp(ord(c), e, n) for c in code]
    encrypted_hex = ','.join(str(i) for i in encrypted_values)
    decrypt_func = random_name()
    
    output_code = f"def {decrypt_func}(encrypted, d, n):\n"
    output_code += "    decrypted = ''.join(chr(pow(int(c), d, n)) for c in encrypted.split(','))\n"
    output_code += "    return decrypted\n\n"
    output_code += f"_crypted_code = \"{encrypted_hex}\"\n"
    output_code += f"_n = {n}\n"
    output_code += f"_d = {d}\n"
    output_code += f"_decrypted_code = {decrypt_func}(_crypted_code, _d, _n)\n"
    output_code += "exec(_decrypted_code)\n"
    
    return output_code

def encryption_method_4(code):
    """Encryption method 4: XOR with key array."""
    key = [random.randint(1, 255) for _ in range(16)]
    encrypted_values = [ord(code[i]) ^ key[i % len(key)] for i in range(len(code))]
    encrypted_hex = ','.join(str(i) for i in encrypted_values)
    key_hex = ','.join(str(k) for k in key)
    decrypt_func = random_name()
    
    output_code = f"def {decrypt_func}(encrypted, key):\n"
    output_code += "    decrypted = ''.join(chr(encrypted[i] ^ key[i % len(key)]) for i in range(len(encrypted)))\n"
    output_code += "    return decrypted\n\n"
    output_code += f"_encrypted_code = [{encrypted_hex}]\n"
    output_code += f"_key = [{key_hex}]\n"
    output_code += f"_decrypted_code = {decrypt_func}(_encrypted_code, _key)\n"
    output_code += "exec(_decrypted_code)\n"
    
    return output_code

# --- AST Transformers ---

class ObfuscateImports(ast.NodeTransformer):
    """
    Process all import statements:
      1. For "import module [as alias]": generate a new random alias and record the mapping for both the module name and the alias.
      2. For "from module import name": for each imported name, generate a new alias and record it for both the original name and its alias (if provided).
      3. For "from module import *": transform it into "import module as <alias>".
    """
    def visit_Import(self, node):
        new_nodes = []
        for alias in node.names:
            module_name = alias.name  # e.g. "numpy"
            new_alias = random_name()
            IMPORT_ALIASES.add(new_alias)
            # Record both the module name and the original alias (if provided) to new_alias.
            IMPORT_MAPPING[module_name] = new_alias
            if alias.asname is not None:
                IMPORT_MAPPING[alias.asname] = new_alias
            encoded = base64.b64encode(module_name.encode('utf-8')).decode('utf-8')
            base64_import = ast.Call(
                func=ast.Name(id="__import__", ctx=ast.Load()),
                args=[ast.Constant(value="base64")],
                keywords=[]
            )
            b64decode_call = ast.Call(
                func=ast.Attribute(
                    value=base64_import,
                    attr="b64decode",
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value=encoded)],
                keywords=[]
            )
            decode_call = ast.Call(
                func=ast.Attribute(
                    value=b64decode_call,
                    attr="decode",
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value="utf-8")],
                keywords=[]
            )
            import_call = ast.Call(
                func=ast.Name(id="__import__", ctx=ast.Load()),
                args=[decode_call],
                keywords=[]
            )
            assign_node = ast.Assign(
                targets=[ast.Name(id=new_alias, ctx=ast.Store())],
                value=import_call
            )
            new_nodes.append(assign_node)
        return new_nodes

    def visit_ImportFrom(self, node):
        if any(alias.name == "*" for alias in node.names):
            # Transform "from module import *" into "import module as <alias>"
            new_alias = random_name()
            IMPORT_ALIASES.add(new_alias)
            IMPORT_MAPPING[node.module] = new_alias
            encoded = base64.b64encode(node.module.encode('utf-8')).decode('utf-8')
            base64_import = ast.Call(
                func=ast.Name(id="__import__", ctx=ast.Load()),
                args=[ast.Constant(value="base64")],
                keywords=[]
            )
            b64decode_call = ast.Call(
                func=ast.Attribute(value=base64_import, attr="b64decode", ctx=ast.Load()),
                args=[ast.Constant(value=encoded)],
                keywords=[]
            )
            decode_call = ast.Call(
                func=ast.Attribute(value=b64decode_call, attr="decode", ctx=ast.Load()),
                args=[ast.Constant(value="utf-8")],
                keywords=[]
            )
            import_call = ast.Call(
                func=ast.Name(id="__import__", ctx=ast.Load()),
                args=[decode_call],
                keywords=[]
            )
            assign_node = ast.Assign(
                targets=[ast.Name(id=new_alias, ctx=ast.Store())],
                value=import_call
            )
            return [assign_node]
        else:
            new_names = []
            for alias in node.names:
                orig_name = alias.name
                # Use the original alias if provided; otherwise, use the original name.
                key = alias.asname if alias.asname is not None else orig_name
                new_alias = random_name()
                # Record both the imported name and its alias (if any) to the new alias.
                IMPORT_MAPPING[orig_name] = new_alias
                IMPORT_MAPPING[key] = new_alias
                new_names.append(ast.alias(name=orig_name, asname=new_alias))
            node.names = new_names
            return node

class ReplaceImportNames(ast.NodeTransformer):
    """
    Replace every occurrence of an original import name with its new alias.
    """
    def visit_Name(self, node):
        if node.id in IMPORT_MAPPING:
            return ast.copy_location(ast.Name(id=IMPORT_MAPPING[node.id], ctx=node.ctx), node)
        return node

class ImportTracker(ast.NodeVisitor):
    """
    Track all imports to ensure consistent variable renaming even when 
    import obfuscation is not explicitly enabled.
    """
    def __init__(self):
        self.imports = {}  # Maps original module/name to its usage
    
    def visit_Import(self, node):
        for alias in node.names:
            # Save the imported name and any alias
            module_name = alias.name
            use_name = alias.asname if alias.asname else module_name
            self.imports[use_name] = module_name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            # Handle "from module import name [as alias]"
            name = alias.name
            use_name = alias.asname if alias.asname else name
            if node.module:
                # For "from module import name", save both the module and the name
                self.imports[use_name] = f"{node.module}.{name}"
            else:
                # For relative imports "from . import name"
                self.imports[use_name] = name
        self.generic_visit(node)

class RenameIdentifiers(ast.NodeTransformer):
    """Rename variable, function, and class names to random strings."""
    def __init__(self, import_aware=True):
        super().__init__()
        self.mapping = {}
        self.reserved = set(dir(__import__('builtins'))) | {
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else",
            "except", "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
            "return", "try", "while", "with", "yield"
        }
        
        # Track all imports if import-aware mode is enabled
        if import_aware:
            self.reserved.update(IMPORT_ALIASES)
            self.reserved.update(IMPORT_MAPPING.keys())
            
            # Track direct import references
            self.import_mapping = {}  # Maps original imported names to their new names
            self.import_references = set()  # Set of all imported names we've seen
        else:
            self.import_mapping = {}
            self.import_references = set()
        
    def _new_name(self, old_name):
        if old_name in self.mapping:
            return self.mapping[old_name]
        new = random_name()
        self.mapping[old_name] = new
        return new
    
    def visit_Import(self, node):
        # Track imported names
        for alias in node.names:
            module_name = alias.name
            use_name = alias.asname if alias.asname else module_name
            # Store the used import name
            self.import_references.add(use_name)
            # If this is a name we'll reference later, map it consistently
            if use_name not in self.import_mapping:
                self.import_mapping[use_name] = self._new_name(use_name)
        # Continue with normal processing
        return self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        # Track names from "from module import name"
        for alias in node.names:
            name = alias.name
            use_name = alias.asname if alias.asname else name
            # Store the used import name
            self.import_references.add(use_name)
            # If this is a name we'll reference later, map it consistently
            if use_name not in self.import_mapping:
                self.import_mapping[use_name] = self._new_name(use_name)
        # Continue with normal processing
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        node.name = self._new_name(node.name)
        node.args = self.visit(node.args)
        node.body = [self.visit(stmt) for stmt in node.body]
        return node

    def visit_ClassDef(self, node):
        node.name = self._new_name(node.name)
        node.body = [self.visit(stmt) for stmt in node.body]
        return node

    def visit_Name(self, node):
        # Do not rename names that are import aliases (they've been replaced)
        if node.id in IMPORT_MAPPING.values():
            return node
            
        # Special handling for imported names
        if node.id in self.import_references:
            # Use the consistent mapping for imported names
            node.id = self.import_mapping[node.id]
            return node
            
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
            if node.id not in self.reserved:
                node.id = self._new_name(node.id)
        return node

    def visit_arg(self, node):
        if node.arg not in self.reserved:
            node.arg = self._new_name(node.arg)
        return node

class EncryptStrings(ast.NodeTransformer):
    """Replace string literals with a runtime call to decode a Base64 string."""
    def __init__(self):
        self.in_docstring = False
        
    def visit_Module(self, node):
        # Process children
        self.generic_visit(node)
        return node
        
    def visit_FunctionDef(self, node):
        # Check for docstring
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            # Skip the docstring
            docstring = node.body[0]
            # Process everything after the docstring
            for item in node.body[1:]:
                self.visit(item)
            # Return with the docstring preserved
            return node
        else:
            # No docstring, process normally
            self.generic_visit(node)
            return node
    
    def visit_ClassDef(self, node):
        # Handle docstrings the same way as in functions
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            # Skip the docstring
            docstring = node.body[0]
            # Process everything after the docstring
            for item in node.body[1:]:
                self.visit(item)
            # Return with the docstring preserved
            return node
        else:
            # No docstring, process normally
            self.generic_visit(node)
            return node
        
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            # Check if this node is in an expression statement directly under a function/class/module
            # which would make it a docstring - we leave those unchanged
            if self.in_docstring:
                return node
                
            try:
                # Simple strings - encode them
                encoded = encode_string(node.value)
                # Parse the encoded string into an AST expression
                new_node = ast.parse(encoded, mode='eval').body
                return ast.copy_location(new_node, node)
            except Exception:
                # If any errors, return the original
                return node
        return node
        
class DynamicFunctionBody(ast.NodeTransformer):
    """
    Wrap the original function body with dynamic execution.
    """
    def visit_FunctionDef(self, node):
        # Create a dummy opaque if-statement with randomized values (for obfuscation purposes)
        random_condition_value = random.randint(1, 1000)
        random_message = ''.join(random.choices(string.ascii_letters, k=random.randint(3, 10)))
        
        # Create a variety of dummy statements to avoid repetitive patterns
        dummy_type = random.choice(["if", "while", "try", "assert"])
        
        if dummy_type == "if":
            # Random comparison with a value that will always be false
            op = random.choice([">", "<", "==", "!=", ">=", "<="])
            val1 = random.randint(1, 100)
            val2 = val1
            if op == ">": val2 = val1 + random.randint(1, 10)
            elif op == "<": val2 = val1 - random.randint(1, 10)
            elif op == "==": val2 = val1 + 1
            elif op == "!=": val2 = val1
            elif op == ">=": val2 = val1 + random.randint(1, 10)
            elif op == "<=": val2 = val1 - random.randint(1, 10)
            
            dummy_if = ast.parse(f"if ({val1} {op} {val2}):\n    print('{random_message}')").body[0]
        elif dummy_type == "while":
            # While with a condition that will never execute
            dummy_if = ast.parse(f"while False:\n    print('{random_message}')").body[0]
        elif dummy_type == "try":
            # Try-except with an illegal operation inside that will never execute
            dummy_if = ast.parse(f"try:\n    if False:\n        x = 1/0\nexcept ZeroDivisionError:\n    pass").body[0]
        else:  # assert
            # Assert with a condition that will always be true
            dummy_if = ast.parse(f"assert True, '{random_message}'").body[0]
        
        # Check for docstring
        has_docstring = (node.body and isinstance(node.body[0], ast.Expr) and 
                         isinstance(node.body[0].value, ast.Constant) and 
                         isinstance(node.body[0].value.value, str))
        
        if has_docstring:
            # Separate the docstring from the function body
            docstring = node.body[0]
            func_body = node.body[1:]
        else:
            # No docstring, encode the whole body
            func_body = node.body
            
        # Generate a random name for the inner function
        inner_func_name = random_name()
        result_var = random_name()
            
        # Create an inner function AST node
        inner_func = ast.FunctionDef(
            name=inner_func_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None
            ),
            body=func_body,
            decorator_list=[],
            returns=None
        )
        
        # Call the inner function and assign the result
        call_and_assign = ast.Assign(
            targets=[ast.Name(id=result_var, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id=inner_func_name, ctx=ast.Load()),
                args=[],
                keywords=[]
            )
        )
        
        # Return the result
        return_stmt = ast.Return(
            value=ast.Name(id=result_var, ctx=ast.Load())
        )
        
        # Combine all the statements
        if has_docstring:
            node.body = [docstring, dummy_if, inner_func, call_and_assign, return_stmt]
        else:
            node.body = [dummy_if, inner_func, call_and_assign, return_stmt]
        
        ast.fix_missing_locations(node)
        return node

class InsertJunkCode(ast.NodeTransformer):
    """
    Insert randomized, do-nothing code into the module at both the beginning and end.
    """
    def __init__(self, num_statements=100, pep8_compliant=True, junk_at_end=True, verbose=False):
        self.num_statements = num_statements
        self.pep8_compliant = pep8_compliant
        self.junk_at_end = junk_at_end
        self.verbose = verbose

    def visit_Module(self, node):
        if self.verbose:
            print(Fore.YELLOW + f"[INFO] Generating {self.num_statements} junk code statements...")
        
        # Calculate how many statements to put at the beginning and end
        begin_statements = self.num_statements // 2
        end_statements = self.num_statements - begin_statements
        
        total_statements_added = 0
        
        # Generate junk code for the beginning
        begin_junk = generate_random_blob_code(begin_statements)
        
        # Generate junk code for the end (if enabled)
        end_junk_ast = None
        if self.junk_at_end:
            end_junk = generate_random_blob_code(end_statements)
            try:
                end_junk_ast = ast.parse(end_junk)
                total_statements_added += len(end_junk_ast.body)
            except SyntaxError:
                if self.verbose:
                    print(Fore.YELLOW + "[WARNING] End junk code had syntax errors. Trying in smaller chunks...")
                end_statements_list = []
                # Try smaller chunks
                for i in range(10):
                    small_junk = generate_random_blob_code(end_statements // 10)
                    try:
                        small_junk_ast = ast.parse(small_junk)
                        end_statements_list.extend(small_junk_ast.body)
                        total_statements_added += len(small_junk_ast.body)
                    except SyntaxError:
                        continue
                end_junk_ast = ast.Module(body=end_statements_list, type_ignores=[])
        
        # Make sure the beginning junk code can be parsed
        try:
            begin_junk_ast = ast.parse(begin_junk)
            total_statements_added += len(begin_junk_ast.body)
            
            # Add junk code to the beginning of the module
            if self.junk_at_end and end_junk_ast and end_junk_ast.body:
                # Add junk to both beginning and end
                node.body = begin_junk_ast.body + node.body + end_junk_ast.body
                if self.verbose:
                    print(Fore.GREEN + f"[SUCCESS] Added {total_statements_added} junk statements")
            else:
                # Add junk only to the beginning
                node.body = begin_junk_ast.body + node.body
                if self.verbose:
                    print(Fore.GREEN + f"[SUCCESS] Added {total_statements_added} junk statements")
                
        except SyntaxError:
            # If there's a syntax error in the junk code, try with smaller chunks
            if self.verbose:
                print(Fore.YELLOW + "[WARNING] Junk code had syntax errors. Trying with smaller chunks...")
            begin_statements_list = []
            
            # Generate smaller chunks of junk code
            for i in range(10):  # Try to create 10 smaller chunks
                small_junk = generate_random_blob_code(begin_statements // 10)  # Split into 10 chunks
                try:
                    small_junk_ast = ast.parse(small_junk)
                    begin_statements_list.extend(small_junk_ast.body)
                    total_statements_added += len(small_junk_ast.body)
                except SyntaxError:
                    if self.verbose:
                        print(Fore.YELLOW + f"[WARNING] Chunk {i+1}/10: Syntax error, skipping")
                    continue  # Skip this chunk
            
            # Add the valid junk to the beginning and end of the module
            if begin_statements_list:
                if self.junk_at_end and end_junk_ast and end_junk_ast.body:
                    # Add junk to both beginning and end
                    node.body = begin_statements_list + node.body + end_junk_ast.body
                    if self.verbose:
                        print(Fore.GREEN + f"[SUCCESS] Added {total_statements_added} junk statements")
                else:
                    # Add junk only to the beginning
                    node.body = begin_statements_list + node.body
                    if self.verbose:
                        print(Fore.GREEN + f"[SUCCESS] Added {total_statements_added} junk statements")
            else:
                if self.verbose:
                    print(Fore.YELLOW + "[WARNING] Could not generate valid junk code for the beginning. Proceeding without it.")
                
                # If we at least have end junk, add that
                if self.junk_at_end and end_junk_ast and end_junk_ast.body:
                    node.body = node.body + end_junk_ast.body
                    if self.verbose:
                        print(Fore.GREEN + f"[SUCCESS] Added {total_statements_added} junk statements")
        
        return node

class ImportRenamer(ast.NodeTransformer):
    """Rename import statements themselves even without full import obfuscation."""
    def __init__(self, mapping=None):
        self.mapping = mapping or {}
    
    def visit_Import(self, node):
        for alias in node.names:
            # For each imported module, generate a new name if needed
            module_name = alias.name
            if alias.asname:
                # If there's an explicit alias, update it
                if alias.asname in self.mapping:
                    alias.asname = self.mapping[alias.asname]
            else:
                # If there's no alias, the module name itself is used
                if module_name in self.mapping:
                    # Create an alias for the module
                    alias.asname = self.mapping[module_name]
        return node
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            # For imported names, check if we should rename
            if alias.asname:
                # If there's an explicit alias, update it
                if alias.asname in self.mapping:
                    alias.asname = self.mapping[alias.asname]
            else:
                # If no alias, the name itself is used
                if alias.name in self.mapping:
                    # Create an alias for the imported name
                    alias.asname = self.mapping[alias.name]
        return node

def set_parent_nodes(tree):
    """Set the parent attribute for all nodes in the tree."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return tree

# --- Main processing function with enhanced encryption ---
def obfuscate_file(input_file, output_file, args):
    """
    Obfuscate a Python file with advanced techniques.
    
    Args:
        input_file (str): Path to the input Python file
        output_file (str): Path to write the obfuscated output
        args: Command line arguments
    """
    if args.verbose:
        print(Fore.CYAN + f"[INFO] Reading input file: {input_file}")
    else:
        print(Fore.CYAN + f"Processing {input_file}...")
        
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    # Apply transformations based on command line arguments
    if args.remove_comments:
        if args.verbose:
            print(Fore.YELLOW + "[INFO] Removing comments and extra whitespace...")
        source_no_comments = remove_comments(source)
    else:
        source_no_comments = source

    if args.verbose:
        print(Fore.YELLOW + "[INFO] Parsing source into AST...")
    tree = ast.parse(source_no_comments, filename=input_file)
    
    # Set parent nodes for docstring detection
    if args.verbose:
        print(Fore.YELLOW + "[INFO] Setting parent nodes for AST...")
    set_parent_nodes(tree)

    # Apply junk code if specified
    if args.junk_code > 0:
        if args.verbose:
            print(Fore.YELLOW + f"[INFO] Inserting {args.junk_code} junk code statements...")
        tree = InsertJunkCode(
            num_statements=args.junk_code, 
            pep8_compliant=True,
            junk_at_end=True,
            verbose=args.verbose
        ).visit(tree)

    # First extract import information
    import_tracker = ImportTracker()
    import_tracker.visit(tree)

    # Apply import obfuscation if specified
    if args.obfuscate_imports:
        if args.verbose:
            print(Fore.YELLOW + "[INFO] Obfuscating import statements...")
        tree = ObfuscateImports().visit(tree)
        if args.verbose:
            print(Fore.YELLOW + "[INFO] Replacing original import names with aliases...")
        tree = ReplaceImportNames().visit(tree)
        
    # Apply identifier renaming if specified
    if args.identifier_rename:
        if args.obfuscate_imports:
            # In this case, RenameIdentifiers can use the global IMPORT_MAPPING
            if args.verbose:
                print(Fore.YELLOW + "[INFO] Renaming identifiers...")
            tree = RenameIdentifiers(import_aware=True).visit(tree)
        else:
            # Otherwise, RenameIdentifiers needs to handle imports itself
            if args.verbose:
                print(Fore.YELLOW + "[INFO] Renaming identifiers (with import tracking)...")
            rename_identifiers = RenameIdentifiers(import_aware=False)
            tree = rename_identifiers.visit(tree)
            
            # Now rename the import statements to match
            if args.verbose:
                print(Fore.YELLOW + "[INFO] Renaming import statements...")
            tree = ImportRenamer(rename_identifiers.import_mapping).visit(tree)
    
    if args.verbose:
        print(Fore.YELLOW + "[INFO] Encrypting strings...")
    tree = EncryptStrings().visit(tree)
    
    # Apply function body wrapping if specified
    if args.dynamic_exec:
        if args.verbose:
            print(Fore.YELLOW + "[INFO] Wrapping function bodies with dynamic exec...")
        tree = DynamicFunctionBody().visit(tree)
    
    if args.verbose:
        print(Fore.YELLOW + "[INFO] Fixing missing locations in AST...")
    ast.fix_missing_locations(tree)

    if args.verbose:
        print(Fore.YELLOW + "[INFO] Unparsing AST to source code...")
    obfuscated_code = astunparse.unparse(tree)

    if args.verbose:
        print(Fore.YELLOW + "[INFO] Fixing slice syntax issues...")
    obfuscated_code = fix_slice_syntax(obfuscated_code)

    # Apply encryption layers if requested
    if args.encrypt > 0:
        if args.verbose:
            print(Fore.YELLOW + f"[INFO] Applying {args.encrypt} encryption layers...")
        for i in range(args.encrypt):
            method = random.randint(1, 4)
            if method == 1:
                if args.verbose:
                    print(Fore.YELLOW + f"[INFO] Applying encryption method 1 (layer {i+1}/{args.encrypt})...")
                obfuscated_code = encryption_method_1(obfuscated_code)
            elif method == 2:
                if args.verbose:
                    print(Fore.YELLOW + f"[INFO] Applying encryption method 2 (layer {i+1}/{args.encrypt})...")
                obfuscated_code = encryption_method_2(obfuscated_code)
            elif method == 3:
                if args.verbose:
                    print(Fore.YELLOW + f"[INFO] Applying encryption method 3 (layer {i+1}/{args.encrypt})...")
                obfuscated_code = encryption_method_3(obfuscated_code)
            else:
                if args.verbose:
                    print(Fore.YELLOW + f"[INFO] Applying encryption method 4 (layer {i+1}/{args.encrypt})...")
                obfuscated_code = encryption_method_4(obfuscated_code)

    if args.verbose:
        print(Fore.YELLOW + f"[INFO] Writing obfuscated code to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(obfuscated_code)
    print(Fore.GREEN + f"[SUCCESS] Obfuscated file written to {output_file}")
    
    # Summary message
    tech_applied = []
    if args.all:
        tech_applied.append("all techniques")
    else:
        if args.remove_comments:
            tech_applied.append("comment removal")
        if args.junk_code > 0:
            tech_applied.append(f"{args.junk_code} junk statements")
        if args.obfuscate_imports:
            tech_applied.append("import obfuscation")
        if args.identifier_rename:
            tech_applied.append("identifier renaming")
        if args.dynamic_exec:
            tech_applied.append("dynamic function execution")
    
    if args.encrypt > 0:
        tech_applied.append(f"{args.encrypt} encryption layers")
    
    tech_str = ", ".join(tech_applied)
    print(Fore.GREEN + f"[SUCCESS] Obfuscation complete with {tech_str}")

# --- Main ---
if __name__ == "__main__":
    # If no arguments were provided, print banner and usage only
    if len(sys.argv) == 1:
        print(BANNER)
        print(f"{Fore.YELLOW}Usage: {Fore.WHITE}python pyfuscator.py [options] input_file output_file{Style.RESET_ALL}")
        print(f"\nUse {Fore.GREEN}-h{Style.RESET_ALL} or {Fore.GREEN}--help{Style.RESET_ALL} for more information.")
        print(f"\nMade by {Fore.CYAN}@spiegelin{Style.RESET_ALL}")
        sys.exit(0)
    
    # If help is requested, print banner first
    if "-h" in sys.argv or "--help" in sys.argv:
        print(BANNER)
    
    # Create the argument parser with colored help
    parser = argparse.ArgumentParser(
        prog="pyfuscator.py",
        description=f"Made by {Fore.CYAN}@spiegelin{Style.RESET_ALL}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''{Fore.GREEN}Examples:{Style.RESET_ALL}
  # Basic obfuscation with identifier renaming and 2 encryption layers
  {Fore.YELLOW}python pyfuscator.py -i -e 2 input.py output.py{Style.RESET_ALL}
  
  # Maximum obfuscation with all features enabled
  {Fore.YELLOW}python pyfuscator.py -i -e 3 -j 300 -r -o -d input.py output.py{Style.RESET_ALL}
  
  # Only identifier renaming
  {Fore.YELLOW}python pyfuscator.py -i input.py output.py{Style.RESET_ALL}
  
  # Only add junk code
  {Fore.YELLOW}python pyfuscator.py -j 150 input.py output.py{Style.RESET_ALL}
  
  # With verbose logging
  {Fore.YELLOW}python pyfuscator.py -v -i -e 1 -j 50 input.py output.py{Style.RESET_ALL}
  
  # Apply all obfuscation techniques except encryption
  {Fore.YELLOW}python pyfuscator.py -a input.py output.py{Style.RESET_ALL}
  
  # Apply all techniques with 2 encryption layers
  {Fore.YELLOW}python pyfuscator.py -a -e 2 input.py output.py{Style.RESET_ALL}'''
    )
    
    # Add arguments with colored help text
    parser.add_argument("input_file", nargs="?", 
                        help=f"{Fore.CYAN}Input Python file to obfuscate{Style.RESET_ALL}")
    parser.add_argument("output_file", nargs="?", 
                        help=f"{Fore.CYAN}Output file for obfuscated code{Style.RESET_ALL}")
    
    parser.add_argument("-e", "--encrypt", type=int, default=0, metavar="NUM",
                        help=f"{Fore.GREEN}Apply NUM layers of encryption (less than 5 is recommended){Style.RESET_ALL}")
    
    parser.add_argument("-j", "--junk-code", type=int, default=0, metavar="NUM",
                        help=f"{Fore.GREEN}Insert NUM random junk statements{Style.RESET_ALL}")
    
    parser.add_argument("-r", "--remove-comments", action="store_true",
                        help=f"{Fore.GREEN}Remove comments from the original code{Style.RESET_ALL}")
    
    parser.add_argument("-o", "--obfuscate-imports", action="store_true",
                        help=f"{Fore.GREEN}Obfuscate import statements and their references{Style.RESET_ALL}")
    
    parser.add_argument("-i", "--identifier-rename", action="store_true",
                        help=f"{Fore.GREEN}Rename variables, functions and class names{Style.RESET_ALL}")
    
    parser.add_argument("-d", "--dynamic-exec", action="store_true",
                        help=f"{Fore.GREEN}Wrap function bodies with dynamic execution{Style.RESET_ALL}")
    
    parser.add_argument("-a", "--all", action="store_true",
                        help=f"{Fore.GREEN}Apply all obfuscation techniques except encryption{Style.RESET_ALL}")
    
    parser.add_argument("-v", "--verbose", action="store_true",
                        help=f"{Fore.GREEN}Log every step of the obfuscation process{Style.RESET_ALL}")

    # Parse arguments
    args = parser.parse_args()
    
    # When --all is specified, enable all other options except encryption
    if args.all:
        args.junk_code = args.junk_code or 200  # Use 200 as default if not specified
        args.remove_comments = True
        args.obfuscate_imports = True
        args.identifier_rename = True
        args.dynamic_exec = True
    
    # Check if required arguments are provided
    if not args.input_file or not args.output_file:
        print(Fore.RED + "Error: Both input and output files must be specified.")
        parser.print_help()
        sys.exit(1)
    
    # Ensure at least one obfuscation method is selected
    if not (args.encrypt > 0 or args.junk_code > 0 or args.remove_comments or 
            args.obfuscate_imports or args.identifier_rename or args.dynamic_exec):
        print(Fore.RED + "Error: At least one obfuscation method must be selected.")
        print(Fore.YELLOW + "Use one or more of: -e, -j, -r, -o, -i, -d, or -a")
        parser.print_help()
        sys.exit(1)
    
    # Apply selected obfuscation techniques
    obfuscate_file(args.input_file, args.output_file, args)