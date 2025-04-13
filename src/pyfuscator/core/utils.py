"""
Utility functions for PyFuscator.
"""
import ast
import base64
import random
import string
import re
import io
import tokenize

def random_name(length: int = 8) -> str:
    """
    Generate a random variable name that's a valid Python identifier.
    Ensures it's not a Python keyword and starts with a letter.
    
    Args:
        length: Length of the random name
        
    Returns:
        A random string suitable as a Python identifier
    """
    # List of Python keywords to avoid
    python_keywords = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
        'with', 'yield'
    }
    
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

def encode_string(s: str) -> str:
    """
    Encode a string to base64 and create a decode expression.
    
    Args:
        s: String to encode
        
    Returns:
        Python code to decode the encoded string at runtime
    """
    encoded = base64.b64encode(s.encode('utf-8')).decode('utf-8')
    return f"__import__('base64').b64decode('{encoded}').decode('utf-8')"

def wrap_with_exec(code_str: str) -> str:
    """
    Wrap code string with exec() in base64 encoding.
    
    Args:
        code_str: Python code to wrap
        
    Returns:
        Code string wrapped with exec
    """
    b64_code = base64.b64encode(code_str.encode('utf-8')).decode('utf-8')
    return f"exec(__import__('base64').b64decode('{b64_code}').decode('utf-8'), globals(), locals())"

def validate_python_code(code_str: str) -> bool:
    """
    Validate if the provided string is valid Python code.
    
    Args:
        code_str: Python code string to validate
        
    Returns:
        True if code is valid, False otherwise
    """
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def generate_random_statement() -> str:
    """
    Generate a random Python statement that follows PEP 8 style guidelines.
    
    Returns:
        A random, syntactically valid Python statement
    """
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
    
    for _ in range(max_attempts):
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

def generate_random_blob_code(num_statements: int = 100) -> str:
    """
    Generate valid Python code following PEP 8 style guidelines.
    
    Args:
        num_statements: Number of statements to generate
        
    Returns:
        A string containing random valid Python code
    """
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

def remove_comments(source: str) -> str:
    """
    Remove comments and docstrings from Python source code while preserving functionality.
    
    String literals that are not docstrings (for example, those in print() calls or assignments)
    are preserved.
    
    Args:
        source: Source code with comments and docstrings
        
    Returns:
        Source code with comments and docstrings removed
    """
    result = []
    io_obj = io.StringIO(source)
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0

    # Generate tokens from the source
    tokens = tokenize.generate_tokens(io_obj.readline)
    for tok in tokens:
        token_type = tok.type
        token_string = tok.string
        start_line, start_col = tok.start
        end_line, end_col = tok.end

        # Maintain spacing by inserting spaces if there's a gap between tokens.
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            result.append(" " * (start_col - last_col))

        # Skip comments completely.
        if token_type == tokenize.COMMENT:
            pass
        # For string tokens, determine if they are docstrings.
        elif token_type == tokenize.STRING:
            # A docstring is typically the first statement in a module, function, or class,
            # which comes right after an INDENT or at the beginning of the file.
            if prev_toktype == tokenize.INDENT or start_col == 0:
                # Skip docstrings.
                pass
            else:
                # Otherwise, keep the string literal.
                result.append(token_string)
        else:
            result.append(token_string)

        prev_toktype = token_type
        last_lineno = end_line
        last_col = end_col

    return "".join(result)

def fix_slice_syntax(code: str) -> str:
    """
    Fixes extra outer parentheses around slice expressions in subscript operations.
    
    Args:
        code: Code with potential slice syntax issues
        
    Returns:
        Fixed code with correct slice syntax
    """
    pattern = re.compile(r'(\[)\(\s*(.*?)\s*\)(\])', re.DOTALL)
    fixed_code = pattern.sub(r'\1\2\3', code)
    return fixed_code

def set_parent_nodes(tree: ast.AST) -> ast.AST:
    """
    Set the parent attribute for all nodes in the tree.
    
    Args:
        tree: AST to set parent nodes for
        
    Returns:
        AST with parent nodes set
    """
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return tree 


def generate_random_comment(self) -> str:
    """Generate a random, nonsensical comment."""
    # Determine the number of words in the phrase
    num_words = random.randint(2, 5)
    words = []
    for _ in range(num_words):
        # Determine the length of each word
        word_length = random.randint(3, 10)
        # Generate a random word consisting of lowercase letters
        word = ''.join(random.choices(string.ascii_lowercase, k=word_length))
        words.append(word)
    # Combine the words into a phrase
    return ' '.join(words)
