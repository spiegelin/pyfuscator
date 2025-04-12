"""
PowerShell junk code insertion transformer.
"""
import random
import string
from typing import List, Optional, Dict

from pyfuscator.core.utils import random_name
from pyfuscator.log_utils import logger

class InsertJunkCode:
    """Transformer that inserts non-functional junk code into PowerShell scripts."""
    
    def __init__(self, num_statements: int = 5, junk_at_beginning: bool = True, 
                 junk_at_end: bool = True, junk_in_functions: bool = False):
        """
        Initialize the transformer.
        
        Args:
            num_statements: Number of junk statements to insert
            junk_at_beginning: Whether to insert junk at the beginning
            junk_at_end: Whether to insert junk at the end
            junk_in_functions: Whether to insert junk in functions
        """
        self.num_statements = num_statements
        self.junk_at_beginning = junk_at_beginning
        self.junk_at_end = junk_at_end
        self.junk_in_functions = junk_in_functions
        self.statements_added = 0
    
    def transform(self, content: str) -> str:
        """
        Transform the PowerShell script by inserting junk code.
        
        Args:
            content: The PowerShell script content
            
        Returns:
            Transformed content with junk code
        """
        self.statements_added = 0
        
        if not content.strip():
            return content
            
        transformed = content
        
        # Add junk at the beginning
        if self.junk_at_beginning:
            beginning_junk = self._generate_junk_code(
                max(1, self.num_statements // 2)
            )
            transformed = beginning_junk + "\n\n" + transformed
            
        # Add junk at the end
        if self.junk_at_end:
            end_junk = self._generate_junk_code(
                max(1, self.num_statements // 2)
            )
            transformed = transformed + "\n\n" + end_junk
            
        # TODO: Add junk in functions if junk_in_functions is True
        # This would require more sophisticated parsing to find function bodies
        
        logger.info(f"Inserted {self.statements_added} junk statements in PowerShell script")
        return transformed
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about junk code insertion.
        
        Returns:
            Dict with statistics about junk statements added
        """
        return {
            "junk_statements": self.statements_added
        }
    
    def _generate_junk_code(self, num_statements: int) -> str:
        """
        Generate junk code with a specified number of statements.
        
        Args:
            num_statements: Number of junk statements to generate
            
        Returns:
            String containing junk code
        """
        junk_statements = []
        
        for _ in range(num_statements):
            # Choose a random junk code generator
            generator = random.choice([
                self._generate_variable_assignment,
                self._generate_condition,
                self._generate_array_manipulation,
                self._generate_function_declaration,
                self._generate_try_catch,
                self._generate_switch_statement,
                self._generate_hash_table
            ])
            
            junk_statements.append(generator())
            self.statements_added += 1
            
        # Add comments to make it look more legitimate
        junk_with_comments = []
        for statement in junk_statements:
            # 30% chance to add a comment before the statement
            if random.random() < 0.3:
                junk_with_comments.append(f"# {self._generate_comment()}")
            
            junk_with_comments.append(statement)
            
        return "\n".join(junk_with_comments)
    
    def _generate_comment(self) -> str:
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
    
    def _generate_variable_assignment(self) -> str:
        """Generate a random variable assignment statement."""
        var_name = f"${random_name(5)}"
        
        # Choose a random value type
        value_type = random.choice(["string", "number", "boolean", "array", "null"])
        
        if value_type == "string":
            value = f"'{random_name(8)}'"
        elif value_type == "number":
            value = str(random.randint(1, 1000))
        elif value_type == "boolean":
            value = random.choice(["$true", "$false"])
        elif value_type == "array":
            elements = [str(random.randint(1, 100)) for _ in range(random.randint(2, 5))]
            value = f"@({', '.join(elements)})"
        else:  # null
            value = "$null"
            
        return f"{var_name} = {value}"
    
    def _generate_condition(self) -> str:
        """Generate a random conditional statement."""
        var_name = f"${random_name(5)}"
        value = random.randint(1, 100)
        
        condition = random.choice([
            f"{var_name} -eq {value}",
            f"{var_name} -ne {value}",
            f"{var_name} -gt {value}",
            f"{var_name} -lt {value}",
            f"{var_name} -ge {value}",
            f"{var_name} -le {value}"
        ])
        
        # Create a simple if statement
        return f"if ({condition}) {{ {self._generate_variable_assignment()} }}"
    
    def _generate_array_manipulation(self) -> str:
        """Generate random array manipulation code that won't cause runtime errors."""
        array_name = f"${random_name(5)}"
        elements = [str(random.randint(1, 100)) for _ in range(random.randint(3, 7))]
        array_init = f"{array_name} = @({', '.join(elements)})"
        
        # Create array and choose a safe operation - with no output
        operations = [
            # Simple array initialization - always safe
            array_init,
            
            # Silent array indexing with assignment to variable (no output)
            f"{array_init}\nif ({array_name}.Length -gt 0) {{ ${random_name(5)} = {array_name}[0] }}",
            
            # Silent array operations with assignment (no output)
            f"{array_init}\n${random_name(5)} = {array_name} | ForEach-Object {{ $_ * 2 }}",
            
            # Silent filtering with assignment (no output)
            f"{array_init}\n${random_name(5)} = {array_name} | Where-Object {{ $_ -gt {random.randint(1, 50)} }}"
        ]
        
        return random.choice(operations)
    
    def _generate_function_declaration(self) -> str:
        """Generate a random function declaration."""
        func_name = f"Get-{random_name(8)}"
        param_name = f"${random_name(5)}"
        var_name = f"${random_name(5)}"
        
        # Create a simple function - no output
        return f"""function {func_name} {{
    param(
        [Parameter(Mandatory=$false)]
        [string]{param_name} = '{random_name(5)}'
    )
    
    {self._generate_variable_assignment()}
    return ${random_name(5)}
}}"""
    
    def _generate_try_catch(self) -> str:
        """Generate a random try-catch block with no output."""
        # Remove Write-Error and replace with silent operation
        return f"""try {{
    {self._generate_variable_assignment()}
    {self._generate_variable_assignment()}
}} catch {{
    ${random_name(5)} = $false
}}"""
    
    def _generate_switch_statement(self) -> str:
        """Generate a random switch statement."""
        var_name = f"${random_name(5)}"
        value = random.randint(1, 5)
        
        cases = []
        for i in range(1, 6):
            cases.append(f"""{i} {{ {self._generate_variable_assignment()} }}""")
            
        cases_str = "\n    ".join(cases)
        
        return f"""switch ({value}) {{
    {cases_str}
    default {{ {self._generate_variable_assignment()} }}
}}"""
    
    def _generate_hash_table(self) -> str:
        """Generate a random hash table."""
        hash_name = f"${random_name(5)}"
        
        keys = [random_name(5) for _ in range(random.randint(2, 5))]
        values = [
            f"'{random_name(8)}'", 
            str(random.randint(1, 100)), 
            random.choice(["$true", "$false"]),
            f"@({random.randint(1, 10)}, {random.randint(1, 10)})"
        ]
        
        entries = []
        for key in keys:
            entries.append(f"{key} = {random.choice(values)}")
            
        entries_str = "; ".join(entries)
        
        return f"{hash_name} = @{{ {entries_str} }}" 