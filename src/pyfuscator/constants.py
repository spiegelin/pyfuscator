"""
Constants used throughout PyFuscator.
"""
from colorama import Fore, Style

# Banner for the help menu with Rich markup formatting
BANNER = """[red]
             __                  _           
  _ __ _  _ / _|_  _ ___ __ __ _| |_ ___ _ _ 
 | '_ \ || |  _| || (_-</ _/ _` |  _/ _ \ '_|
 | .__/\_, |_|  \_,_/__/\__\__,_|\__\___/_|  
 |_|   |__/                                  [/]

 Made by [cyan]@spiegelin[/]"""

# Python keywords set (used in multiple places)
PYTHON_KEYWORDS = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
    'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
    'with', 'yield'
}

# Default values
DEFAULT_JUNK_STATEMENTS = 200
DEFAULT_MAX_ATTEMPTS = 3
MAX_SEARCH_ATTEMPTS = 10  # For finding syntax-valid junk code

# Help text colors
COLOR_TITLE = Fore.CYAN
COLOR_OPTION = Fore.GREEN
COLOR_COMMAND = Fore.YELLOW
COLOR_RESET = Style.RESET_ALL
COLOR_ERROR = Fore.RED
COLOR_SUCCESS = Fore.GREEN
COLOR_INFO = Fore.YELLOW

# Usage examples
EXAMPLES = """  # Basic obfuscation with identifier renaming and 2 encryption layers
  pyfuscator -i -e 2 input.py output.py
  
  # Maximum obfuscation with all features enabled
  pyfuscator -i -e 3 -j 300 -r -o -d input.py output.py
  
  # Only identifier renaming
  pyfuscator -i input.py output.py
  
  # Only add junk code
  pyfuscator -j 150 input.py output.py
  
  # With verbose logging
  pyfuscator -v -i -e 1 -j 50 input.py output.py
  
  # Apply all obfuscation techniques except encryption
  pyfuscator -a input.py output.py
  
  # Apply all techniques with 2 encryption layers
  pyfuscator -a -e 2 input.py output.py"""
