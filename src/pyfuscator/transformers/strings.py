"""
AST transformer for string encryption.
"""
import ast
from typing import Optional, Any
import base64

from pyfuscator.core.utils import encode_string

class EncryptStrings(ast.NodeTransformer):
    """Transformer that encrypts string literals."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.count = 0  # Track number of encrypted strings
        self.in_docstring = False
        
    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process module nodes, preserving module-level docstrings."""
        # Skip module docstring if present
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
            docstring = node.body[0]
            node.body = node.body[1:]
            node = self.generic_visit(node)
            node.body.insert(0, docstring)
            return node
        return self.generic_visit(node)
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Skip docstrings in function definitions."""
        # Skip docstring if present
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
            docstring = node.body[0]
            node.body = node.body[1:]
            node = self.generic_visit(node)
            node.body.insert(0, docstring)
            return node
        return self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Skip docstrings in class definitions."""
        # Same logic as visit_FunctionDef for now
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
            docstring = node.body[0]
            node.body = node.body[1:]
            node = self.generic_visit(node)
            node.body.insert(0, docstring)
            return node
        return self.generic_visit(node)
    
    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        """Skip f-strings to avoid issues with astunparse."""
        return node
    
    def visit_FormattedValue(self, node: ast.FormattedValue) -> ast.FormattedValue:
        """Skip formatted values in f-strings."""
        return node
    
    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Encrypt string constants."""
        if isinstance(node.value, str):
            # Skip empty strings
            if not node.value.strip():
                return node
                
            # Skip docstrings (already handled in visit_Module, visit_FunctionDef, and visit_ClassDef)
            # Skip strings that are part of annotations
            # Skip strings with special characters or multiline strings
            if (
                hasattr(node, 'parent') and 
                (isinstance(node.parent, ast.AnnAssign) or 
                 isinstance(node.parent, ast.arg)) or
                '\n' in node.value or
                '\\' in node.value  # Skip strings with escape characters
            ):
                return node
                
            # Encrypt the string
            encoded = base64.b64encode(node.value.encode()).decode()
            expr = ast.parse(f"__import__('base64').b64decode('{encoded}').decode()").body[0].value
            self.count += 1  # Increment the counter
            return expr
        return node 