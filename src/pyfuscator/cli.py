"""Command-line interface for the PyFuscator tool."""
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich import print as rprint

from pyfuscator import __version__
from pyfuscator.config import ObfuscationConfig
from pyfuscator.core.obfuscator import Obfuscator, obfuscate_file
from pyfuscator.log_utils import configure_logger, setup_logger
from pyfuscator.constants import BANNER

# Initialize Typer app
app = typer.Typer(
    help="Just another code obfuscation tool",
    add_completion=False
)

console = Console()
# Default logger instance - will be configured later
logger = setup_logger()


def _read_file(file_path: str) -> str:
    """Read content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Content of the file as a string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise typer.Exit(code=1)


def _write_file(file_path: str, content: str) -> None:
    """Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    try:
        with open(file_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        raise typer.Exit(code=1)


def _display_stats(stats: Dict[str, Any], language: str, verbose: bool = False) -> None:
    """Display obfuscation statistics.
    
    Args:
        stats: Statistics from the obfuscation process
        language: The programming language that was obfuscated
        verbose: Whether to show detailed statistics
    """
    if not verbose:
        return
        
    # Create a stats table with different color
    stats_table = Table(box=ROUNDED, title="Obfuscation Stats", title_style="bold magenta", 
                       show_header=False, border_style="magenta")
    
    # Get file sizes for comparison
    input_size = stats.get('input_size', 0)
    output_size = stats.get('output_size', 0)
    size_diff = output_size - input_size
    percent = (size_diff / input_size) * 100 if input_size > 0 else 0
    
    # Add rows to the stats table
    stats_table.add_column("Metric", style="dim")
    stats_table.add_column("Value", style="magenta")
    
    stats_table.add_row("Original file size", f"{input_size:,} bytes")
    stats_table.add_row("Obfuscated file size", f"{output_size:,} bytes")
    stats_table.add_row("Size difference", f"{size_diff:+,} bytes ({percent:.1f}%)")
    
    # Display the stats table
    console.print(stats_table)
    console.print("[magenta]Obfuscation complete![/]")


def _detect_language(file_path: str) -> str:
    """Detect the programming language based on the file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language ("python" or "powershell") or an empty string if unable to detect
    """
    ext = Path(file_path).suffix.lower()
    
    if ext in [".py", ".pyw"]:
        return "python"
    elif ext in [".ps1", ".psm1", ".psd1"]:
        return "powershell"
    else:
        return ""


def custom_help_callback(ctx: typer.Context, value: bool):
    """Custom callback for the help option to display banner before help text."""
    if not value or ctx.resilient_parsing:
        return value
    
    # Print banner
    console.print(BANNER)
    console.print("")
    
    # Get and print help text
    console.print(ctx.get_help())
    
    raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version information and exit"),
    help: bool = typer.Option(False, "--help", "-h", help="Show this message and exit.", callback=custom_help_callback, is_eager=True),
):
    """
    PyFuscator - A powerful code obfuscator for Python and PowerShell scripts.
    
    Use commands to access language-specific options:
    
    - python: obfuscate Python code
    - powershell: obfuscate PowerShell code
    """
    
    if version:
        console.print(f"PyFuscator version: {__version__}")
        raise typer.Exit()
    
    # If no subcommand was called, display help
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print("")
        console.print(" [bold][yellow]Usage:[/][/bold] pyfuscator [OPTIONS] COMMAND [ARGS]...\n")
        console.print(" For more information, use: [bold]pyfuscator --help[/]")
        #console.print(ctx.get_usage())
        raise typer.Exit()


@app.command("python")
def python_command(
    input_file: str = typer.Argument(..., help="Input Python file to obfuscate"),
    output_file: str = typer.Argument(..., help="Output file for the obfuscated code"),
    remove_comments: bool = typer.Option(True, "-r", "--remove-comments", help="Remove comments from the code"),
    junk_code: int = typer.Option(0, "-j", "--junk-code", help="Insert random junk statements"),
    obfuscate_imports: bool = typer.Option(False, "-o", "--obfuscate-imports", help="Obfuscate import statements"),
    rename_identifiers: bool = typer.Option(False, "-i", "--identifier-rename", help="Rename variables, functions and class names"),
    dynamic_exec: bool = typer.Option(False, "-d", "--dynamic-exec", help="Wrap function bodies with dynamic execution"),
    encrypt_strings: bool = typer.Option(False, "-s", "--encrypt-strings", help="Encrypt string literals"),
    encrypt: int = typer.Option(0, "-e", "--encrypt", help="Apply layers of encryption (0-5)"),
    all_obfuscations: bool = typer.Option(False, "-a", "--all", help="Apply all obfuscation techniques except encryption"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed logs during obfuscation"),
    help: bool = typer.Option(False, "--help", "-h", help="Show Python obfuscation options.", callback=custom_help_callback, is_eager=True),
):
    """Obfuscate Python code with various techniques."""
    # Configure logging
    global logger
    configure_logger(verbose=verbose)
    logger = setup_logger(verbose=verbose)

    # Print banner
    console.print(BANNER)
    console.print("")
    
    # Notify about first-time execution performance
    console.print("[yellow]Note:[/] First-time execution might take longer due to module initialization and AST processing.\n")
    
    # Validate input and output files
    input_path = Path(input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        raise typer.Exit(code=1)
        
    # If verbose, log all enabled options
    if verbose:
        logger.info(f"Processing {input_file}")
        if remove_comments:
            logger.info(f"Comment removal enabled (default)")
        if junk_code > 0:
            logger.info(f"Will add {junk_code} junk statements")
        if obfuscate_imports:
            logger.info(f"Import obfuscation enabled")
        if rename_identifiers:
            logger.info(f"Identifier renaming enabled")
        if dynamic_exec:
            logger.info(f"Dynamic function execution enabled")
        if encrypt_strings:
            logger.info(f"String encryption enabled")
        if encrypt > 0:
            logger.info(f"Will apply {encrypt} encryption layers")
        if all_obfuscations:
            logger.info(f"All techniques enabled")
    
    # Execute the obfuscation
    try:
        # Tell user what's happening
        logger.info(f"Reading input file: {input_file}")
        
        # Use the obfuscate_file function which reads/writes files and handles errors
        result = obfuscate_file(
            input_file=input_file,
            output_file=output_file,
            language="python",
            remove_comments=remove_comments,
            rename_identifiers=rename_identifiers or all_obfuscations,
            junk_code=junk_code or (200 if all_obfuscations else 0),
            obfuscate_imports=obfuscate_imports or all_obfuscations,
            dynamic_execution=dynamic_exec or all_obfuscations,
            encrypt_strings=encrypt_strings or all_obfuscations,
            encrypt_layers=encrypt,
            verbose=verbose
        )
        
        # Get file sizes for statistics
        input_size = Path(input_file).stat().st_size
        output_size = Path(output_file).stat().st_size
        
        # Add to stats
        stats = result.get('stats', {}) if isinstance(result, dict) else {}
        stats['input_size'] = input_size
        stats['output_size'] = output_size
        
        # Always show success message
        logger.info(f"Writing obfuscated code to {output_file}")
        logger.success(f"Obfuscation completed successfully")
        console.print(f"[green]✓ Obfuscated file written to {output_file}[/]")
        
        # Summarize techniques used
        tech_applied = []
        if all_obfuscations:
            tech_applied.append("all techniques")
        else:
            if remove_comments:
                tech_applied.append("comment removal")
            if junk_code > 0:
                tech_applied.append(f"{junk_code} junk statements")
            if obfuscate_imports:
                tech_applied.append("import obfuscation")
            if rename_identifiers:
                tech_applied.append("identifier renaming")
            if dynamic_exec:
                tech_applied.append("dynamic function execution")
            if encrypt_strings:
                tech_applied.append("string encryption")
        
        if encrypt > 0:
            tech_applied.append(f"{encrypt} encryption layers")
        
        tech_str = ", ".join(tech_applied)
        console.print(f"[green]✓ Successfully applied:[/] {tech_str}")
        
        # Display statistics only in verbose mode
        if verbose:
            console.print("")
            _display_stats(stats, "python", verbose)
        
    except Exception as e:
        logger.error(f"Obfuscation failed: {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command("powershell")
def powershell_command(
    input_file: str = typer.Argument(..., help="Input PowerShell file to obfuscate"),
    output_file: str = typer.Argument(..., help="Output file for the obfuscated code"),
    remove_comments: bool = typer.Option(True, "-r", "--remove-comments", help="Remove comments from the code"),
    junk_code: int = typer.Option(0, "-j", "--junk-code", help="Insert random junk statements"),
    tokenize_commands: bool = typer.Option(False, "-c", "--tokenize-commands", help="Tokenize and obfuscate PowerShell commands"),
    rename_identifiers: bool = typer.Option(False, "-i", "--identifier-rename", help="Rename variables and function names"),
    dotnet_methods: bool = typer.Option(False, "-d", "--dotnet-methods", help="(Experimental) Use .NET methods for obfuscation"),
    secure_strings: bool = typer.Option(False, "-s", "--secure-strings", help="(Experimental) Use SecureString for string obfuscation"),
    string_divide: bool = typer.Option(False, "-sd", "--string-divide", help="Divide strings into concatenated parts"),
    script_encrypt: bool = typer.Option(False, "-e", "--encrypt", help="Encrypt the entire script with SecureString"),
    base64: bool = typer.Option(False, "-b", "--base64", help="Encode individual commands with Base64"),
    base64_full: bool = typer.Option(False, "--base64-full", help="Encode the entire script with Base64"),
    ads: bool = typer.Option(False, "--ads", help="(Experimental) Store scripts in Alternate Data Streams (Windows only)"),
    lower_entropy: bool = typer.Option(False, "-l", "--lower-entropy", help="Apply entropy reduction techniques"),
    all_obfuscations: bool = typer.Option(False, "-a", "--all", help="Apply the following techniques in this order: comment removal, identifier renaming, junk code insertion (200), lower entropy, tokenization, string division, Base64 encode"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed logs during obfuscation"),
    help: bool = typer.Option(False, "--help", "-h", help="Show PowerShell obfuscation options.", callback=custom_help_callback, is_eager=True),
):
    """Obfuscate PowerShell code with various techniques."""
    # Configure logging
    global logger
    configure_logger(verbose=verbose)
    logger = setup_logger(verbose=verbose)

    # Print banner
    console.print(BANNER)
    console.print("")
    
    # Notify about first-time execution performance
    console.print("[yellow]Note:[/] First-time execution might take longer due to module initialization and AST processing.\n")
    
    # Validate input and output files
    input_path = Path(input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        raise typer.Exit(code=1)
        
    # If verbose, log all enabled options
    if verbose:
        logger.info(f"Processing {input_file}")
        if remove_comments:
            logger.info(f"Comment removal enabled (default)")
        if junk_code > 0:
            logger.info(f"Will add {junk_code} junk statements")
        if tokenize_commands:
            logger.info(f"Command tokenization enabled")
        if rename_identifiers:
            logger.info(f"Identifier renaming enabled")
        if dotnet_methods:
            logger.info(f"Using .NET methods")
        if secure_strings:
            logger.info(f"SecureString obfuscation enabled")
        if string_divide:
            logger.info(f"String division enabled")
        if base64:
            logger.info(f"Base64 command encoding enabled")
        if base64_full:
            logger.info(f"Full script Base64 encoding enabled")
        if script_encrypt:
            logger.info(f"Full script encryption enabled")
        if lower_entropy:
            logger.info(f"Lower entropy transformation enabled")
        if all_obfuscations:
            logger.info(f"All specified obfuscation techniques enabled in exact sequence")
    
    # Execute the obfuscation
    try:
        # Tell user what's happening
        logger.info(f"Reading input file: {input_file}")
        
        # Use the obfuscate_file function which reads/writes files and handles errors
        result = obfuscate_file(
            input_file=input_file,
            output_file=output_file,
            language="powershell",
            # Order is important as per the requirement - EXACTLY this sequence:
            # 1. Comment removal (-r)
            remove_comments=remove_comments or all_obfuscations,
            # 2. Identifier renaming (-i)
            rename_identifiers=rename_identifiers or all_obfuscations,
            # 3. Junk code insertion (-j 200)
            junk_code=junk_code or (200 if all_obfuscations else 0),
            # 4. Lower entropy (-l)
            lower_entropy=lower_entropy or all_obfuscations,
            # 5. Tokenization (-c)
            tokenize_commands=tokenize_commands or all_obfuscations,
            # 6. String division (-sd)
            string_divide=string_divide or all_obfuscations,
            # 7. Base64 encode (-b)
            base64_commands=base64 or all_obfuscations,
            # Excluded from all_obfuscations:
            secure_strings=secure_strings,
            dotnet_methods=dotnet_methods,
            base64_full=base64_full,
            script_encrypt=script_encrypt,
            use_ads=ads,
            verbose=verbose
        )
        
        # Get file sizes for statistics
        input_size = Path(input_file).stat().st_size
        output_size = Path(output_file).stat().st_size
        
        # Add to stats
        stats = result.get('stats', {}) if isinstance(result, dict) else {}
        stats['input_size'] = input_size
        stats['output_size'] = output_size
        
        # Always show success message
        logger.info(f"Writing obfuscated code to {output_file}")
        logger.success(f"Obfuscation completed successfully")
        console.print(f"[green]✓ Obfuscated file written to {output_file}[/]")
        
        # Summarize techniques used
        tech_applied = []
        if all_obfuscations:
            tech_applied.append("standard obfuscation sequence (in order: comment removal, identifier renaming, junk code, lower entropy, tokenization, string division, base64)")
        else:
            if remove_comments:
                tech_applied.append("comment removal")
            if junk_code > 0:
                tech_applied.append(f"{junk_code} junk statements")
            if tokenize_commands:
                tech_applied.append("command tokenization")
            if rename_identifiers:
                tech_applied.append("identifier renaming")
            if dotnet_methods:
                tech_applied.append(".NET methods")
            if secure_strings:
                tech_applied.append("SecureString obfuscation")
            if string_divide:
                tech_applied.append("string division")
            if base64:
                tech_applied.append("Base64 command encoding")
            if script_encrypt:
                tech_applied.append("script encryption")
            if lower_entropy:
                tech_applied.append("lower entropy transformation")
            if ads:
                tech_applied.append("alternate data streams")
        
        tech_str = ", ".join(tech_applied)
        console.print(f"[green]✓ Successfully applied:[/] {tech_str}")
        
        # Display statistics only in verbose mode
        if verbose:
            console.print("")
            _display_stats(stats, "powershell", verbose)
        
    except Exception as e:
        logger.error(f"Obfuscation failed: {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
