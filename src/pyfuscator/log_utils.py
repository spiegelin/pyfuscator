"""
Logging functionality for PyFuscator.
"""
from colorama import Fore, Style
import logging
from typing import Optional, Set
import sys

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""
    
    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        """Format log record with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
            if not record.msg.startswith(Fore.GREEN) and not record.msg.startswith(Fore.RED):
                record.msg = f"{self.COLORS[levelname]}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

class Logger:
    """Simple logger wrapper with colored output."""
    
    # These are the only messages that should be shown in non-verbose mode
    ESSENTIAL_MESSAGES = {
        "Reading input file:",
        "Writing obfuscated code to",
        "Auto-detected Python",
        "Auto-detected PowerShell",
        "Could not determine script language",
        "Using specified script language",
        "PowerShell obfuscation is not yet implemented"
    }
    
    def __init__(self, verbose: bool = False):
        """Initialize logger with verbosity setting."""
        self.verbose = verbose
        
    def debug(self, message: str) -> None:
        """Log debug message (only in verbose mode)."""
        if self.verbose:
            print(f"{Fore.BLUE}[DEBUG] {message}{Style.RESET_ALL}")
    
    def info(self, message: str) -> None:
        """Log info message."""
        # In verbose mode, show all info messages with [INFO] tag
        if self.verbose:
            print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")
        else:
            # In non-verbose mode, only show essential messages with consistent brackets
            show_message = False
            for essential_prefix in self.ESSENTIAL_MESSAGES:
                if message.startswith(essential_prefix):
                    show_message = True
                    break
                    
            if show_message:
                # Add brackets for consistency in UI
                print(f"{Fore.CYAN}[•] {message}{Style.RESET_ALL}")
            
    def success(self, message: str) -> None:
        """Log success message."""
        if self.verbose:
            print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")
        else:
            # Success messages are always shown in non-verbose mode with ✓ prefix
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")
    
    def error(self, message: str) -> None:
        """Log error message."""
        print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")
        
def setup_logger(verbose: bool = False) -> Logger:
    """Create and configure logger instance."""
    return Logger(verbose)
    
# Default logger instance
logger = Logger()

# Create a logger instance
pyfuscator_logger = logging.getLogger('pyfuscator')

def configure_logger(verbose: bool = False) -> logging.Logger:
    """Configure the logger with appropriate handlers and formatters.
    
    Args:
        verbose: Whether to enable verbose logging
        
    Returns:
        The configured logger
    """
    # Clear any existing handlers
    pyfuscator_logger.handlers = []
    
    # Set logging level based on verbosity
    if verbose:
        pyfuscator_logger.setLevel(logging.DEBUG)
    else:
        pyfuscator_logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatters
    if verbose:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Add formatter to console handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    pyfuscator_logger.addHandler(console_handler)
    
    return pyfuscator_logger

# Export the logger instance
__all__ = ['logger', 'configure_logger', 'setup_logger']
