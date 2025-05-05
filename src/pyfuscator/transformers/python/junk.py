"""
Junk code insertion transformer.
"""
import ast

from pyfuscator.core.utils import generate_random_blob_code
from pyfuscator.log_utils import logger

class InsertJunkCode(ast.NodeTransformer):
    """
    Insert randomized, do-nothing code into the module at both the beginning and end.
    """
    def __init__(self, num_statements=100, pep8_compliant=True, junk_at_end=True, verbose=False):
        self.num_statements = num_statements
        self.pep8_compliant = pep8_compliant
        self.junk_at_end = junk_at_end
        self.verbose = verbose
        self.total_statements_added = 0

    def visit_Module(self, node):
        """
        Visit the module and insert junk code at the beginning and end.
        """
        total_statements_added = 0
        
        # Calculate how many statements to put at the beginning and end
        begin_statements = self.num_statements // 2
        end_statements = self.num_statements - begin_statements
        
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
                logger.warning("End junk code had syntax errors. Trying in smaller chunks...")
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
            else:
                # Add junk only to the beginning
                node.body = begin_junk_ast.body + node.body
                
        except SyntaxError:
            # If there's a syntax error in the junk code, try with smaller chunks
            logger.warning("Junk code had syntax errors. Trying with smaller chunks...")
            begin_statements_list = []
            
            # Generate smaller chunks of junk code
            for i in range(10):  # Try to create 10 smaller chunks
                small_junk = generate_random_blob_code(begin_statements // 10)  # Split into 10 chunks
                try:
                    small_junk_ast = ast.parse(small_junk)
                    begin_statements_list.extend(small_junk_ast.body)
                    total_statements_added += len(small_junk_ast.body)
                except SyntaxError:
                    logger.warning(f"Chunk {i+1}/10: Syntax error, skipping")
                    continue  # Skip this chunk
            
            # Add the valid junk to the beginning and end of the module
            if begin_statements_list:
                if self.junk_at_end and end_junk_ast and end_junk_ast.body:
                    # Add junk to both beginning and end
                    node.body = begin_statements_list + node.body + end_junk_ast.body
                else:
                    # Add junk only to the beginning
                    node.body = begin_statements_list + node.body
            else:
                logger.warning("Could not generate valid junk code for the beginning. Proceeding without it.")
                
                # If we at least have end junk, add that
                if self.junk_at_end and end_junk_ast and end_junk_ast.body:
                    node.body = node.body + end_junk_ast.body
        
        # Store the number of statements added for reporting in obfuscator.py
        self.total_statements_added = total_statements_added
        
        return node 