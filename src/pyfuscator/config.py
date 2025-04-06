"""
Configuration management for PyFuscator.
"""
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field

class ObfuscationConfig(BaseModel):
    """Configuration for the obfuscation process."""
    
    # Input/Output
    input_file: str = Field(..., description="Input Python file to obfuscate")
    output_file: str = Field(..., description="Output file for obfuscated code")
    
    # Obfuscation techniques
    encrypt: int = Field(0, description="Number of encryption layers to apply", ge=0, le=5)
    junk_code: int = Field(0, description="Number of junk statements to insert", ge=0)
    remove_comments: bool = Field(True, description="Remove comments from the original code (enabled by default)")
    obfuscate_imports: bool = Field(False, description="Obfuscate import statements and their references")
    identifier_rename: bool = Field(False, description="Rename variables, functions and class names")
    dynamic_exec: bool = Field(False, description="Wrap function bodies with dynamic execution")
    encrypt_strings: bool = Field(False, description="Encrypt string literals in the code")
    all_techniques: bool = Field(False, description="Apply all obfuscation techniques except encryption")
    
    # Runtime options
    verbose: bool = Field(False, description="Log every step of the obfuscation process")
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
        extra = "forbid"
        
    def apply_all_techniques(self) -> "ObfuscationConfig":
        """Apply all obfuscation techniques (except encryption)."""
        self.junk_code = self.junk_code or 200
        self.remove_comments = True
        self.obfuscate_imports = True
        self.identifier_rename = True
        self.dynamic_exec = True
        self.encrypt_strings = True
        return self
        
    def has_any_technique(self) -> bool:
        """Check if at least one obfuscation technique is selected."""
        return (
            self.encrypt > 0 or 
            self.junk_code > 0 or 
            self.remove_comments or
            self.obfuscate_imports or
            self.identifier_rename or
            self.dynamic_exec or
            self.encrypt_strings
        )
    
    def get_applied_techniques(self) -> List[str]:
        """Get a list of applied techniques for logging."""
        techniques = []
        
        if self.all_techniques:
            techniques.append("all techniques")
        else:
            # Comment removal is now always applied
            techniques.append("comment removal")
            if self.junk_code > 0:
                techniques.append(f"{self.junk_code} junk statements")
            if self.obfuscate_imports:
                techniques.append("import obfuscation")
            if self.identifier_rename:
                techniques.append("identifier renaming")
            if self.dynamic_exec:
                techniques.append("dynamic function execution")
            if self.encrypt_strings:
                techniques.append("string encryption")
        
        if self.encrypt > 0:
            techniques.append(f"{self.encrypt} encryption layers")
            
        return techniques
