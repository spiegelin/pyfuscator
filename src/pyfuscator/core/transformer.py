"""
Base transformer class for all transformers.
"""
from typing import Dict, Any

class Transformer:
    """Base class for all code transformers."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.stats = {}
        
    def transform(self, content: str) -> str:
        """
        Apply transformation to the content.
        
        Args:
            content: The content to transform
            
        Returns:
            The transformed content
        """
        raise NotImplementedError("Transformer subclasses must implement transform method")
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the transformation.
        
        Returns:
            Dictionary with transformation statistics
        """
        return self.stats 