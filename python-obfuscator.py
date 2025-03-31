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

from colorama import Fore, Style, init
init(autoreset=True)

# Global sets/dictionaries for import obfuscation.
IMPORT_ALIASES = set()
IMPORT_MAPPING = {}  # Maps original import names (or original alias) to new random alias.

# --- Helper functions ---

def random_name(length=8):
    # Ensure the first character is a letter.
    first = random.choice(string.ascii_letters)
    rest = ''.join(random.choices(string.ascii_letters + string.digits, k=length-1))
    return first + rest

def encode_string(s):
    encoded = base64.b64encode(s.encode('utf-8')).decode('utf-8')
    return f"(__import__('base64').b64decode('{encoded}').decode('utf-8'))"

def wrap_with_exec(code_str):
    b64_code = base64.b64encode(code_str.encode('utf-8')).decode('utf-8')
    # Merge globals() and locals() so that dynamically executed code can access outer variables.
    return f"exec(__import__('base64').b64decode('{b64_code}').decode('utf-8'), {{**globals(), **locals()}})"



def generate_random_statement():
    """Generate a random Python statement that does nothing."""
    statement_type = random.choice(["assignment", "loop", "if", "function_def", "pass_stmt"])
    indent = "    "
    if statement_type == "assignment":
        var_name = random_name()
        value = random.randint(0, 1000)
        return f"{var_name} = {value}"
    elif statement_type == "loop":
        loop_var = random_name()
        loop_count = random.randint(5, 20)
        inner_var = random_name()
        return f"for {loop_var} in range({loop_count}):\n{indent}{inner_var} = {loop_var} + {random.randint(1, 10)}"
    elif statement_type == "if":
        condition = random.randint(0, 100)
        return f"if {condition} % 2 == 0:\n{indent}pass"
    elif statement_type == "function_def":
        func_name = random_name()
        arg_count = random.randint(0, 3)
        args = [random_name() for _ in range(arg_count)]
        body_lines = [f"{indent}pass" for _ in range(random.randint(1, 5))]
        return f"def {func_name}({', '.join(args)}):\n" + "\n".join(body_lines)
    elif statement_type == "pass_stmt":
        return "pass"
    return ""

def generate_random_blob_code(num_statements=50):
    """Generate a bunch of random, do-nothing Python code as a string."""
    code_lines = [generate_random_statement() for _ in range(num_statements)]
    return "\n\n".join(code_lines)

def remove_comments(source):
    output = io.StringIO()
    last_lineno = -1
    last_col = 0
    tokgen = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokgen:
        token_type, token_string, start, end, line = tok
        lineno, col = start
        if lineno > last_lineno:
            last_col = 0
        if token_type == tokenize.COMMENT:
            continue
        else:
            if col > last_col:
                output.write(" " * (col - last_col))
            output.write(token_string)
        last_lineno, last_col = end
    return output.getvalue()

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


class RenameIdentifiers(ast.NodeTransformer):
    """Rename variable, function, and class names to random strings."""
    def __init__(self):
        super().__init__()
        self.mapping = {}
        self.reserved = set(dir(__import__('builtins'))) | {
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else",
            "except", "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
            "return", "try", "while", "with", "yield"
        }
        self.reserved.update(IMPORT_ALIASES)
        self.reserved.update(IMPORT_MAPPING.keys())
    def _new_name(self, old_name):
        if old_name in self.mapping:
            return self.mapping[old_name]
        new = random_name()
        self.mapping[old_name] = new
        return new

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
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            new_node = ast.parse(encode_string(node.value), mode='eval').body
            return ast.copy_location(new_node, node)
        return node

class DynamicFunctionBody(ast.NodeTransformer):
    """
    Wrap the original function body into an inner function so that any 'return'
    statements are properly contained. This prevents "return outside function" errors.
    """
    def visit_FunctionDef(self, node):
        # Unparse the original function body.
        original_body = astunparse.unparse(ast.Module(body=node.body, type_ignores=[]))
        # Generate a random name for the inner function.
        inner_func_name = random_name()
        # Wrap the original body inside an inner function definition with proper indentation.
        wrapped_code = f"def {inner_func_name}():\n" + "\n".join("    " + line for line in original_body.splitlines())
        # Call the inner function.
        wrapped_code += f"\n{inner_func_name}()"
        # Create a dummy opaque if-statement (for obfuscation purposes).
        dummy_if = ast.parse("if (42==43):\n    print('junk')").body[0]
        # Create an exec() call that decodes and executes the wrapped code.
        exec_call = ast.parse(wrap_with_exec(wrapped_code), mode='exec').body
        # Replace the original function body with the dummy and the exec() call.
        node.body = [dummy_if] + exec_call
        return node



class InsertJunkCode(ast.NodeTransformer):
    """
    Insert a lot of randomized, do-nothing code into the module.
    """
    def __init__(self, num_statements=100):
        self.num_statements = num_statements

    def visit_Module(self, node):
        junk_code = generate_random_blob_code(self.num_statements)
        junk_ast = ast.parse(junk_code)
        node.body = junk_ast.body + node.body
        return node

# --- Main processing function ---
def obfuscate_file(input_file, output_file):
    print(Fore.CYAN + f"[INFO] Reading input file: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    print(Fore.YELLOW + "[INFO] Removing comments and extra whitespace...")
    source_no_comments = remove_comments(source)

    print(Fore.YELLOW + "[INFO] Parsing source into AST...")
    tree = ast.parse(source_no_comments, filename=input_file)

    print(Fore.YELLOW + "[INFO] Inserting a lot of junk code...")
    tree = InsertJunkCode(num_statements=200).visit(tree) # Increased the number of statements

    print(Fore.YELLOW + "[INFO] Obfuscating import statements...")
    tree = ObfuscateImports().visit(tree)
    print(Fore.YELLOW + "[INFO] Replacing original import names with aliases...")
    tree = ReplaceImportNames().visit(tree)

    print(Fore.YELLOW + "[INFO] Renaming identifiers...")
    tree = RenameIdentifiers().visit(tree)
    print(Fore.YELLOW + "[INFO] Encrypting strings...")
    tree = EncryptStrings().visit(tree)
    print(Fore.YELLOW + "[INFO] Wrapping function bodies with dynamic exec...")
    tree = DynamicFunctionBody().visit(tree)
    ast.fix_missing_locations(tree)

    print(Fore.YELLOW + "[INFO] Unparsing AST to source code...")
    obfuscated_code = astunparse.unparse(tree)

    print(Fore.YELLOW + "[INFO] Fixing slice syntax issues...")
    obfuscated_code = fix_slice_syntax(obfuscated_code)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(obfuscated_code)
    print(Fore.GREEN + f"[SUCCESS] Obfuscated file written to {output_file}")

# --- Main ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(Fore.RED + "Usage: python python-obfuscator.py <input_script.py> <output_script.py>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    obfuscate_file(input_file, output_file)