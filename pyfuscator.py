#!/usr/bin/env python3
"""
Wrapper script to run PyFuscator without installation.
This script allows running the obfuscator directly from the source directory.
"""
import sys
import os
import subprocess

# Get the absolute path to the CLI module
script_dir = os.path.dirname(os.path.abspath(__file__))
cli_path = os.path.join(script_dir, "src", "pyfuscator", "cli.py")

if __name__ == "__main__":
    try:
        # Pass all arguments to the CLI script
        cmd = [sys.executable, cli_path] + sys.argv[1:]
        
        # Run the CLI module as a subprocess
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running PyFuscator: {e}")
        sys.exit(1) 