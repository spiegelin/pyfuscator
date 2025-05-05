"""
AST transformers for function obfuscation.
"""
import ast
import random
import string

class DynamicFunctionBody(ast.NodeTransformer):
    """Wrap function bodies with dynamic execution for obfuscation."""
    
    def __init__(self):
        """Initialize the transformer."""
        super().__init__()
        self.count = 0  # Track number of functions transformed
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Transform function definitions by wrapping the body in a dynamically executed 
        inner function.
        
        Args:
            node: FunctionDef node
            
        Returns:
            Transformed function definition
        """
        # Don't skip small functions for tests to pass
        # But still skip functions with only a docstring
        has_docstring = (len(node.body) > 0 and 
                       isinstance(node.body[0], ast.Expr) and 
                       isinstance(node.body[0].value, ast.Constant) and 
                       isinstance(node.body[0].value.value, str))
                
        if has_docstring and len(node.body) < 2:
            return node
            
        # First, process any inner function definitions or class definitions
        node.body = [self.visit(stmt) for stmt in node.body]
        
        # Create a dummy opaque statement (if, while, try, assert, or multiline)
        # that will never be executed, to make the code harder to follow
        dummy_type = random.choice(["if", "while", "try", "assert", "multiline"])
        dummy_stmt = None
        
        if dummy_type == "if":
            # Create an if statement with a condition that's always False
            dummy_stmt = ast.If(
                test=ast.Compare(
                    left=ast.Constant(value=1),
                    ops=[ast.Gt()],
                    comparators=[ast.Constant(value=100)]
                ),
                body=[
                    ast.Expr(value=ast.Constant(value="This code will never execute"))
                ],
                orelse=[]
            )
        elif dummy_type == "while":
            # Create a while loop that never executes
            dummy_stmt = ast.While(
                test=ast.Compare(
                    left=ast.Constant(value=0),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value=1)]
                ),
                body=[
                    ast.Expr(value=ast.Constant(value="This loop will never execute"))
                ],
                orelse=[]
            )
        elif dummy_type == "try":
            # Create a try-except block with an illegal operation that will not run
            dummy_stmt = ast.Try(
                body=[
                    ast.Expr(value=ast.Constant(value="This try block contains an illegal operation")),
                ],
                handlers=[
                    ast.ExceptHandler(
                        type=ast.Name(id="Exception", ctx=ast.Load()),
                        name=None,
                        body=[
                            ast.Pass()
                        ]
                    )
                ],
                orelse=[],
                finalbody=[]
            )
        elif dummy_type == "assert":
            # Create an assert statement that's always true
            dummy_stmt = ast.Assert(
                test=ast.Compare(
                    left=ast.Constant(value=1),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value=1)]
                ),
                msg=ast.Constant(value="This assert will always pass")
            )
        else:  # multiline
            # Create a complex multiline dummy code that is unreachable
            dummy_stmt = ast.If(
                test=ast.Compare(
                    left=ast.Constant(value=False),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value=True)]
                ),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id="_x", ctx=ast.Store())],
                        value=ast.Constant(value=100)
                    ),
                    ast.Assign(
                        targets=[ast.Name(id="_y", ctx=ast.Store())],
                        value=ast.Constant(value=200)
                    ),
                    ast.Expr(
                        value=ast.BinOp(
                            left=ast.Name(id="_x", ctx=ast.Load()),
                            op=ast.Add(),
                            right=ast.Name(id="_y", ctx=ast.Load())
                        )
                    )
                ],
                orelse=[]
            )
            
        # Check for docstring and separate it from the function body
        new_body = []
        if has_docstring:
            new_body.append(node.body[0])  # Keep the docstring
            function_body = node.body[1:]  # The rest is the actual function body
        else:
            function_body = node.body
            
        # Add the dummy statement to make code analysis harder
        new_body.append(dummy_stmt)
        
        # Generate random names for inner function and result variable
        inner_func_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        result_var = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        # Create an inner function that contains the original function body
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
            body=function_body,
            decorator_list=[],
            returns=None
        )
        
        # Add the inner function definition
        new_body.append(inner_func)
        
        # Call the inner function and assign the result to a variable
        new_body.append(
            ast.Assign(
                targets=[ast.Name(id=result_var, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id=inner_func_name, ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            )
        )
        
        # Return the result from the transformed function
        new_body.append(ast.Return(value=ast.Name(id=result_var, ctx=ast.Load())))
        
        # Replace the function body with our transformation
        node.body = new_body
        
        # Increment the count of transformed functions
        self.count += 1
        
        return node 