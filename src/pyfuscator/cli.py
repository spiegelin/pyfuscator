"""Command-line interface for the PyFuscator tool."""
from pathlib import Path
from typing import Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED
from rich.tree import Tree

from pyfuscator import __version__
from pyfuscator.core.obfuscator import obfuscate_file
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


def _display_rename_map(rename_map: Dict[str, Any], language: str) -> None:
    """Display the identifier renaming map in a hierarchical table.

    Args:
        rename_map: Map of renamed identifiers with their hierarchical relationships
        language: The programming language that was obfuscated
    """
    if not rename_map:
        return

    # Create a tree for hierarchical display
    CYAN = "bold cyan"
    tree = Tree("Renamed Identifiers", style=CYAN)

    if language.lower() == "python":
        # Add classes
        if "Classes" in rename_map and rename_map["Classes"]:
            class_branch = tree.add("Classes", style="bold green")
            for class_name, class_data in rename_map["Classes"].items():
                new_class_name = class_data.get("new_name", "Unknown")
                class_node = class_branch.add(f"[green]{class_name}[/green] → [yellow]{new_class_name}[/yellow]")

                # Add class functions
                if "Functions" in class_data and class_data["Functions"]:
                    for func_name, func_data in class_data["Functions"].items():
                        new_func_name = func_data.get("new_name", "Unknown")
                        func_node = class_node.add(f"[cyan]Function: {func_name}[/cyan] → [yellow]{new_func_name}[/yellow]")

                        # Add function variables
                        if "Variables" in func_data and func_data["Variables"]:
                            for var_name, new_var_name in func_data["Variables"].items():
                                func_node.add(f"[blue]Variable: {var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

                # Add class variables
                if "Variables" in class_data and class_data["Variables"]:
                    for var_name, new_var_name in class_data["Variables"].items():
                        class_node.add(f"[blue]Variable: {var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

        # Add global functions
        if "Functions" in rename_map and rename_map["Functions"]:
            function_branch = tree.add("Global Functions", style=CYAN)
            for func_name, func_data in rename_map["Functions"].items():
                new_func_name = func_data.get("new_name", "Unknown")
                func_node = function_branch.add(f"[cyan]{func_name}[/cyan] → [yellow]{new_func_name}[/yellow]")

                # Add function variables
                if "Variables" in func_data and func_data["Variables"]:
                    for var_name, new_var_name in func_data["Variables"].items():
                        func_node.add(f"[blue]Variable: {var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

        # Add global variables
        if "Variables" in rename_map and rename_map["Variables"]:
            variable_branch = tree.add("Global Variables", style="bold blue")
            for var_name, new_var_name in rename_map["Variables"].items():
                variable_branch.add(f"[blue]{var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

    elif language.lower() == "powershell":
        # Add global functions
        if "Functions" in rename_map and rename_map["Functions"]:
            function_branch = tree.add("Functions", style=CYAN)
            for func_name, func_data in rename_map["Functions"].items():
                new_func_name = func_data.get("new_name", "Unknown")
                func_node = function_branch.add(f"[cyan]{func_name}[/cyan] → [yellow]{new_func_name}[/yellow]")

                # Add function variables
                if "Variables" in func_data and func_data["Variables"]:
                    for var_name, new_var_name in func_data["Variables"].items():
                        func_node.add(f"[blue]{var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

        # Add global variables
        if "Variables" in rename_map and rename_map["Variables"]:
            variable_branch = tree.add("Global Variables", style="bold blue")
            for var_name, new_var_name in rename_map["Variables"].items():
                variable_branch.add(f"[blue]{var_name}[/blue] → [yellow]{new_var_name}[/yellow]")

    # Print the tree
    console.print("")
    console.print(tree)


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
    remove_comments: bool = typer.Option(
        True, "-r", "--remove-comments/--no-remove-comments", help="Remove comments from the code"
    ),
    junk_code: int = typer.Option(0, "-j", "--junk-code", help="Insert random junk statements"),
    obfuscate_imports: bool = typer.Option(
        False, "-o", "--obfuscate-imports", help="Obfuscate import statements"
    ),
    rename_identifiers: bool = typer.Option(
        False, "-i", "--identifier-rename", help="Rename variables, functions and class names"
    ),
    dynamic_exec: bool = typer.Option(
        False, "-d", "--dynamic-exec", help="Wrap function bodies with dynamic execution"
    ),
    encrypt_strings: bool = typer.Option(
        False, "-s", "--encrypt-strings", help="Encrypt string literals"
    ),
    encrypt: int = typer.Option(0, "-e", "--encrypt", help="Apply layers of encryption (0-5)"),
    all_obfuscations: bool = typer.Option(
        False, "-a", "--all", help="Apply all obfuscation techniques except encryption"
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed logs during obfuscation"),
    help: bool = typer.Option(
        False, "--help", "-h",
        help="Show Python obfuscation options.",
        callback=custom_help_callback,
        is_eager=True
    ),
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
            logger.info("Comment removal enabled (default)")
        if junk_code > 0:
            logger.info(f"Will add {junk_code} junk statements")
        if obfuscate_imports:
            logger.info("Import obfuscation enabled")
        if rename_identifiers:
            logger.info("Identifier renaming enabled")
        if dynamic_exec:
            logger.info("Dynamic function execution enabled")
        if encrypt_strings:
            logger.info("String encryption enabled")
        if encrypt > 0:
            logger.info(f"Will apply {encrypt} encryption layers")
        if all_obfuscations:
            logger.info("All techniques enabled")

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
        logger.success("Obfuscation completed successfully")
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

        # Display rename map if identifier renaming is enabled (explicitly or via all_obfuscations)
        if rename_identifiers or all_obfuscations:
            rename_map = stats.get('rename_map', {})
            if rename_map:
                _display_rename_map(rename_map, "python")
            else:
                logger.debug("No rename map found in stats")

        # Display statistics only in verbose mode (after rename map)
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
    remove_comments: bool = typer.Option(
        True, "-r", "--remove-comments/--no-remove-comments", help="Remove comments from the code"
    ),
    junk_code: int = typer.Option(0, "-j", "--junk-code", help="Insert random junk statements"),
    tokenize_commands: bool = typer.Option(
        False, "-c", "--tokenize-commands", help="Tokenize and obfuscate PowerShell commands"
    ),
    rename_identifiers: bool = typer.Option(
        False, "-i", "--identifier-rename", help="Rename variables and function names"
    ),
    dotnet_methods: bool = typer.Option(
        False, "-d", "--dotnet-methods", help="(Experimental) Use .NET methods for obfuscation"
    ),
    secure_strings: bool = typer.Option(
        False, "-s", "--secure-strings", help="(Experimental) Use SecureString for string obfuscation"
    ),
    string_divide: bool = typer.Option(
        False, "-sd", "--string-divide", help="Divide strings into concatenated parts"
    ),
    script_encrypt: bool = typer.Option(
        False, "-e", "--encrypt", help="Encrypt the entire script with SecureString"
    ),
    base64: bool = typer.Option(
        False, "-b", "--base64", help="Encode individual commands with Base64"
    ),
    base64_full: bool = typer.Option(
        False, "--base64-full", help="Encode the entire script with Base64"
    ),
    ads: bool = typer.Option(
        False, "--ads", help="(Experimental) Store scripts in Alternate Data Streams (Windows only)"
    ),
    lower_entropy: bool = typer.Option(
        False, "-l", "--lower-entropy", help="Apply entropy reduction techniques"
    ),
    all_obfuscations: bool = typer.Option(
        False, "-a", "--all", 
        help="Apply the following techniques in this order: comment removal, identifier renaming, "
             "junk code insertion (200), lower entropy, tokenization, string division, Base64 encode"
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed logs during obfuscation"),
    help: bool = typer.Option(
        False, "--help", "-h", 
        help="Show PowerShell obfuscation options.", 
        callback=custom_help_callback, 
        is_eager=True
    ),
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
            logger.info("Comment removal enabled (default)")
        if junk_code > 0:
            logger.info(f"Will add {junk_code} junk statements")
        if tokenize_commands:
            logger.info("Command tokenization enabled")
        if rename_identifiers:
            logger.info("Identifier renaming enabled")
        if dotnet_methods:
            logger.info("Using .NET methods")
        if secure_strings:
            logger.info("SecureString obfuscation enabled")
        if string_divide:
            logger.info("String division enabled")
        if base64:
            logger.info("Base64 command encoding enabled")
        if base64_full:
            logger.info("Full script Base64 encoding enabled")
        if script_encrypt:
            logger.info("Full script encryption enabled")
        if lower_entropy:
            logger.info("Lower entropy transformation enabled")
        if all_obfuscations:
            logger.info("All specified obfuscation techniques enabled in exact sequence")

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
        logger.success("Obfuscation completed successfully")
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

        # Display rename map if identifier renaming is enabled (explicitly or via all_obfuscations)
        if rename_identifiers or all_obfuscations:
            rename_map = stats.get('rename_map', {})
            if rename_map:
                _display_rename_map(rename_map, "powershell")
            else:
                logger.debug("No rename map found in stats")

        # Display statistics only in verbose mode (after rename map)
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
