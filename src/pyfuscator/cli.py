"""
Command-line interface for PyFuscator.
"""
import sys
from pathlib import Path
from typing import Optional, List, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED

from pyfuscator.constants import BANNER
from pyfuscator.core.obfuscator import obfuscate_file
from pyfuscator.log_utils import setup_logger, logger

console = Console()

# Custom callback for the help option
def custom_callback(ctx: typer.Context, param: typer.CallbackParam, value: bool) -> Any:
    if not value or ctx.resilient_parsing:
        return value
    
    # Print banner - use Rich formatting instead of ANSI codes
    console.print(BANNER)
    console.print("")
    
    # Get the regular help text
    help_text = ctx.get_help()
    
    # Print the help text
    console.print(help_text)
    
    ctx.exit()

# Create Typer app with custom help
app = typer.Typer(
    name="pyfuscator",
    help="",
    add_completion=True,
)

# Override the help option to use our custom callback
help_option = typer.Option(
    False, "--help", "-h", 
    help="Show this message and exit.",
    callback=custom_callback,
    is_eager=True
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # Custom help option 
    help: bool = help_option,
    # Input/Output files
    input_file: Optional[Path] = typer.Argument(
        None, help="Input Python file to obfuscate", show_default=False
    ),
    output_file: Optional[Path] = typer.Argument(
        None, help="Output file for obfuscated code", show_default=False
    ),
    # Obfuscation options
    encrypt: int = typer.Option(
        0, "-e", "--encrypt", min=0, max=5,
        help="Apply N layers of encryption (less than 5 is recommended)"
    ),
    junk_code: int = typer.Option(
        0, "-j", "--junk-code", min=0,
        help="Insert N random junk statements"
    ),
    remove_comments: bool = typer.Option(
        True, "-r", "--remove-comments",
        help="Remove comments from the original code (enabled by default)"
    ),
    obfuscate_imports: bool = typer.Option(
        False, "-o", "--obfuscate-imports",
        help="Obfuscate import statements and their references"
    ),
    identifier_rename: bool = typer.Option(
        False, "-i", "--identifier-rename",
        help="Rename variables, functions and class names"
    ),
    dynamic_exec: bool = typer.Option(
        False, "-d", "--dynamic-exec",
        help="Wrap function bodies with dynamic execution"
    ),
    encrypt_strings: bool = typer.Option(
        False, "-s", "--encrypt-strings",
        help="Encrypt string literals with base64 encoding"
    ),
    all_techniques: bool = typer.Option(
        False, "-a", "--all",
        help="Apply all obfuscation techniques except encryption"
    ),
    # Other options
    verbose: bool = typer.Option(
        False, "-v", "--verbose",
        help="Show detailed logs and statistics during obfuscation"
    ),
    version: bool = typer.Option(
        False, "--version",
        help="Show PyFuscator version and exit"
    ),
    # Hide completion options from help
    install_completion: bool = typer.Option(
        False,
        "--install-completion",
        help="Install completion for the current shell.",
        hidden=True,
    ),
    show_completion: bool = typer.Option(
        False,
        "--show-completion",
        help="Show completion for the current shell, to copy it or customize the installation.",
        hidden=True,
    ),
) -> None:
    """
    PyFuscator
    
    Transforms your Python code into a form that is difficult to understand and reverse engineer
    while preserving its original functionality.
    """
    # Set up logger based on verbosity
    global logger
    logger = setup_logger(verbose)
    
    # Show version and exit if requested
    if version:
        from pyfuscator.pyfuscator import __version__
        console.print(BANNER)
        console.print(f"PyFuscator v{__version__}")
        raise typer.Exit()
    
    # Show banner and exit if no arguments
    if ctx.invoked_subcommand is None and not input_file and not output_file:
        console.print(BANNER)
        
        # Show usage
        console.print("\n[bold cyan]Usage:[/] [white]pyfuscator [OPTIONS] INPUT_FILE OUTPUT_FILE[/]")
        console.print("\nUse [green]-h[/] or [green]--help[/] for more information.")
        
        # Exit gracefully
        raise typer.Exit()
    
    # If files are provided, run obfuscation
    if input_file and output_file:
        # Show the banner before starting
        console.print(BANNER)
        console.print("")  # Add line space
        
        # Check if files exist
        if not input_file.exists():
            console.print(f"[bold red]Error:[/] Input file {input_file} does not exist.")
            raise typer.Exit(1)
            
        # Set techniques if --all is used
        if all_techniques:
            remove_comments = True
            junk_code = junk_code or 200  # Use 200 as default if not specified
            obfuscate_imports = True
            identifier_rename = True
            dynamic_exec = True
            encrypt_strings = True
        
        # Check if any obfuscation technique is explicitly selected
        # besides remove_comments (since it's now default)
        explicitly_selected = (
            encrypt > 0 or 
            junk_code > 0 or 
            obfuscate_imports or 
            identifier_rename or 
            dynamic_exec or 
            encrypt_strings
        )
        # Notify about first-time execution performance
        console.print("[yellow]Note:[/] First-time execution might take longer due to module initialization and AST processing.\n")
        
        # We always want to allow running with just -r
        # (or even without any flags, since remove_comments is default)
        if not explicitly_selected and not all_techniques:
            # At this point, we're only applying remove_comments (default)
            if verbose:
                console.print("[cyan][INFO][/] Only applying comment removal (default behavior)")
        
        # Run obfuscation
        try:
            # Only log this in verbose mode
            if verbose:
                console.print(f"[cyan][INFO][/] Processing {input_file}")
                if remove_comments:
                    console.print(f"[cyan][INFO][/] Comment removal enabled (default)")
                if junk_code > 0:
                    console.print(f"[cyan][INFO][/] Will add {junk_code} junk statements")
                if obfuscate_imports:
                    console.print(f"[cyan][INFO][/] Import obfuscation enabled")
                if identifier_rename:
                    console.print(f"[cyan][INFO][/] Identifier renaming enabled")
                if dynamic_exec:
                    console.print(f"[cyan][INFO][/] Dynamic function execution enabled")
                if encrypt_strings:
                    console.print(f"[cyan][INFO][/] String encryption enabled")
                if encrypt > 0:
                    console.print(f"[cyan][INFO][/] Will apply {encrypt} encryption layers")
                if all_techniques:
                    console.print(f"[cyan][INFO][/] All techniques enabled")
            
            obfuscate_file(
                str(input_file),
                str(output_file),
                encrypt=encrypt,
                junk_code=junk_code,
                remove_comments=remove_comments,
                obfuscate_imports=obfuscate_imports,
                identifier_rename=identifier_rename,
                dynamic_exec=dynamic_exec,
                encrypt_strings=encrypt_strings,
                all_techniques=all_techniques,
                verbose=verbose
            )
            
            # Always show the file written message
            console.print(f"[green]✓ Obfuscated file written to {output_file}[/]")
            
            # Summarize techniques used (always show this)
            tech_applied = []
            if all_techniques:
                tech_applied.append("all techniques")
            else:
                # Comment removal is now always applied
                tech_applied.append("comment removal")
                if junk_code > 0:
                    tech_applied.append(f"{junk_code} junk statements")
                if obfuscate_imports:
                    tech_applied.append("import obfuscation")
                if identifier_rename:
                    tech_applied.append("identifier renaming")
                if dynamic_exec:
                    tech_applied.append("dynamic function execution")
                if encrypt_strings:
                    tech_applied.append("string encryption")
            
            if encrypt > 0:
                tech_applied.append(f"{encrypt} encryption layers")
            
            tech_str = ", ".join(tech_applied)
            console.print(f"[green]✓ Successfully applied:[/] {tech_str}")
            
            # Show additional stats in verbose mode
            if verbose:
                console.print("")
                
                # Create a stats table with different color
                stats_table = Table(box=ROUNDED, title="Obfuscation Stats", title_style="bold magenta", 
                                   show_header=False, border_style="magenta")
                
                # Get file sizes for comparison
                input_size = Path(input_file).stat().st_size
                output_size = Path(output_file).stat().st_size
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
                
        except Exception as e:
            console.print(f"[bold red]Error during obfuscation:[/] {str(e)}")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)
    
if __name__ == "__main__":
    app()
