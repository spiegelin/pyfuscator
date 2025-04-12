#!/usr/bin/env python3
"""
Wrapper script for running PyFuscator without installing.
"""
import sys
import os.path
from pathlib import Path

def main():
    """Run PyFuscator as a module."""
    # Add the src directory to sys.path to make the package importable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(script_dir, "src"))
    
    # Check if "obfuscate" is in args and remove it (for backward compatibility)
    if len(sys.argv) > 1 and sys.argv[1] == "obfuscate":
        sys.argv.pop(1)
    
    # Import and run the CLI
    from pyfuscator.cli import app
    app()

if __name__ == "__main__":
    main() 