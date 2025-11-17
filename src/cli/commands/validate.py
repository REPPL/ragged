"""Configuration validation command for ragged CLI.

Validates configuration settings and environment to catch issues early.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
from pydantic import ValidationError

from src.cli.common import click, console
from src.config.settings import Settings, get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command()
@click.option(
    "--fix",
    "-f",
    is_flag=True,
    help="Attempt to automatically fix issues (creates directories, etc.)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation information",
)
def validate(fix: bool, verbose: bool) -> None:
    """Validate ragged configuration and environment.

    Checks for common configuration issues and validates:
      - Configuration file syntax and required settings
      - Directory permissions and accessibility
      - Ollama service connectivity
      - ChromaDB configuration
      - Embedding model availability

    \b
    Examples:
        # Validate configuration
        ragged validate

        # Validate and auto-fix issues
        ragged validate --fix

        # Show detailed validation info
        ragged validate --verbose
    """
    console.print("\n[bold]Ragged Configuration Validation[/bold]\n")

    issues: List[Tuple[str, str, str]] = []  # (severity, category, message)
    warnings: List[Tuple[str, str]] = []  # (category, message)
    fixes_applied: List[str] = []

    # 1. Validate configuration loading
    console.print("[bold cyan]1. Configuration File[/bold cyan]")
    try:
        settings = get_settings()
        console.print("  [green]✓[/green] Configuration loaded successfully")
        if verbose:
            console.print(f"    Config source: {settings.model_config.get('env_file', '.env')}")
    except ValidationError as e:
        console.print("  [red]✗[/red] Configuration validation failed")
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            issues.append(("ERROR", "config", f"{field}: {error['msg']}"))
        console.print(
            "\n[red]Critical configuration errors found. Fix .env file and try again.[/red]\n"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"  [red]✗[/red] Failed to load configuration: {e}")
        issues.append(("ERROR", "config", f"Configuration loading failed: {e}"))
        sys.exit(1)

    # 2. Validate directories
    console.print("\n[bold cyan]2. Directories & Permissions[/bold cyan]")
    directories_ok = _validate_directories(settings, issues, warnings, fixes_applied, fix, verbose)

    # 3. Validate Ollama connectivity
    console.print("\n[bold cyan]3. Ollama Service[/bold cyan]")
    _validate_ollama(settings, issues, warnings, verbose)

    # 4. Validate ChromaDB configuration
    console.print("\n[bold cyan]4. ChromaDB Configuration[/bold cyan]")
    _validate_chromadb(settings, issues, warnings, verbose)

    # 5. Validate embedding model
    console.print("\n[bold cyan]5. Embedding Model[/bold cyan]")
    _validate_embedding_model(settings, issues, warnings, verbose)

    # 6. Validate LLM model
    console.print("\n[bold cyan]6. LLM Model Configuration[/bold cyan]")
    _validate_llm_model(settings, issues, warnings, verbose)

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Validation Summary[/bold]\n")

    errors = [i for i in issues if i[0] == "ERROR"]
    if errors:
        console.print(f"[red]✗ {len(errors)} Error(s) Found:[/red]")
        for _, category, message in errors:
            console.print(f"  • [{category}] {message}")
        console.print()

    if warnings:
        console.print(f"[yellow]⚠ {len(warnings)} Warning(s):[/yellow]")
        for category, message in warnings:
            console.print(f"  • [{category}] {message}")
        console.print()

    if fixes_applied:
        console.print(f"[green]✓ {len(fixes_applied)} Fix(es) Applied:[/green]")
        for fix_msg in fixes_applied:
            console.print(f"  • {fix_msg}")
        console.print()

    if not errors and not warnings:
        console.print("[green]✓ All checks passed![/green]")
        console.print("\nYour ragged configuration is valid and ready to use.")
    elif not errors:
        console.print(
            "[yellow]Configuration is valid but has warnings.[/yellow]"
            "\nRadded should work, but consider addressing the warnings above."
        )
    else:
        console.print(
            "[red]Configuration has errors that must be fixed.[/red]"
            "\nRadded may not work correctly until these issues are resolved."
        )
        sys.exit(1)


def _validate_directories(
    settings: Settings,
    issues: List[Tuple[str, str, str]],
    warnings: List[Tuple[str, str]],
    fixes_applied: List[str],
    fix: bool,
    verbose: bool,
) -> bool:
    """Validate required directories exist and are writable."""
    all_ok = True

    # Check data directory
    data_dir = Path(settings.data_dir)
    if not data_dir.exists():
        if fix:
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"  [green]✓[/green] Data directory created: {data_dir}")
                fixes_applied.append(f"Created data directory: {data_dir}")
            except Exception as e:
                console.print(f"  [red]✗[/red] Cannot create data directory: {e}")
                issues.append(("ERROR", "filesystem", f"Cannot create {data_dir}: {e}"))
                all_ok = False
        else:
            console.print(f"  [red]✗[/red] Data directory does not exist: {data_dir}")
            issues.append(
                ("ERROR", "filesystem", f"Data directory not found: {data_dir} (use --fix to create)")
            )
            all_ok = False
    elif not data_dir.is_dir():
        console.print(f"  [red]✗[/red] Data path exists but is not a directory: {data_dir}")
        issues.append(("ERROR", "filesystem", f"{data_dir} is not a directory"))
        all_ok = False
    elif not os.access(data_dir, os.W_OK):
        console.print(f"  [red]✗[/red] Data directory is not writable: {data_dir}")
        issues.append(("ERROR", "filesystem", f"No write permission for {data_dir}"))
        all_ok = False
    else:
        console.print(f"  [green]✓[/green] Data directory: {data_dir}")
        if verbose:
            console.print(f"    Writable: Yes")
            console.print(f"    Absolute path: {data_dir.resolve()}")

    # Check ChromaDB persistence directory
    chroma_dir = Path(settings.chroma_persist_directory)
    if not chroma_dir.exists():
        if fix:
            try:
                chroma_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"  [green]✓[/green] ChromaDB directory created: {chroma_dir}")
                fixes_applied.append(f"Created ChromaDB directory: {chroma_dir}")
            except Exception as e:
                console.print(f"  [red]✗[/red] Cannot create ChromaDB directory: {e}")
                issues.append(("ERROR", "filesystem", f"Cannot create {chroma_dir}: {e}"))
                all_ok = False
        else:
            console.print(f"  [yellow]⚠[/yellow] ChromaDB directory does not exist: {chroma_dir}")
            warnings.append(
                ("filesystem", f"ChromaDB directory will be created on first use: {chroma_dir}")
            )
    elif not chroma_dir.is_dir():
        console.print(f"  [red]✗[/red] ChromaDB path exists but is not a directory: {chroma_dir}")
        issues.append(("ERROR", "filesystem", f"{chroma_dir} is not a directory"))
        all_ok = False
    elif not os.access(chroma_dir, os.W_OK):
        console.print(f"  [red]✗[/red] ChromaDB directory is not writable: {chroma_dir}")
        issues.append(("ERROR", "filesystem", f"No write permission for {chroma_dir}"))
        all_ok = False
    else:
        console.print(f"  [green]✓[/green] ChromaDB directory: {chroma_dir}")
        if verbose:
            console.print(f"    Writable: Yes")

    return all_ok


def _validate_ollama(
    settings: Settings,
    issues: List[Tuple[str, str, str]],
    warnings: List[Tuple[str, str]],
    verbose: bool,
) -> None:
    """Validate Ollama service connectivity."""
    try:
        # Check if Ollama base URL is accessible
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            console.print(f"  [green]✓[/green] Ollama service reachable at {settings.ollama_base_url}")
            if verbose:
                data = response.json()
                models = data.get("models", [])
                if models:
                    console.print(f"    Available models: {len(models)}")
                    for model in models[:3]:  # Show first 3
                        console.print(f"      - {model.get('name', 'unknown')}")
                    if len(models) > 3:
                        console.print(f"      ... and {len(models) - 3} more")
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Ollama responded with status {response.status_code}"
            )
            warnings.append(("ollama", f"Unexpected status code: {response.status_code}"))
    except httpx.ConnectError:
        console.print(f"  [red]✗[/red] Cannot connect to Ollama at {settings.ollama_base_url}")
        issues.append(
            ("ERROR", "ollama", f"Ollama not reachable at {settings.ollama_base_url}. Is it running?")
        )
    except httpx.TimeoutException:
        console.print(f"  [yellow]⚠[/yellow] Ollama connection timed out")
        warnings.append(("ollama", "Connection timeout - Ollama may be slow or overloaded"))
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Error checking Ollama: {e}")
        warnings.append(("ollama", f"Error validating Ollama: {e}"))


def _validate_chromadb(
    settings: Settings,
    issues: List[Tuple[str, str, str]],
    warnings: List[Tuple[str, str]],
    verbose: bool,
) -> None:
    """Validate ChromaDB configuration."""
    console.print(f"  [green]✓[/green] Collection name: {settings.chroma_collection_name}")

    if verbose:
        console.print(f"    Persist directory: {settings.chroma_persist_directory}")
        console.print(f"    Distance function: {settings.chroma_distance_function}")

    # Validate distance function
    valid_functions = ["cosine", "l2", "ip"]
    if settings.chroma_distance_function not in valid_functions:
        console.print(
            f"  [yellow]⚠[/yellow] Unusual distance function: {settings.chroma_distance_function}"
        )
        warnings.append(
            ("chromadb", f"Distance function '{settings.chroma_distance_function}' is not standard. Valid options: {', '.join(valid_functions)}")
        )


def _validate_embedding_model(
    settings: Settings,
    issues: List[Tuple[str, str, str]],
    warnings: List[Tuple[str, str]],
    verbose: bool,
) -> None:
    """Validate embedding model configuration."""
    console.print(f"  [green]✓[/green] Model type: {settings.embedding_model}")
    console.print(f"  [green]✓[/green] Model name: {settings.embedding_model_name}")

    if verbose:
        console.print(f"    Device: {settings.embedding_device}")
        console.print(f"    Normalize: {settings.embedding_normalize}")

    # Check device setting
    if settings.embedding_device == "cuda":
        console.print("  [yellow]⚠[/yellow] CUDA device configured")
        warnings.append(
            ("embedding", "CUDA device configured - ensure NVIDIA GPU drivers are installed")
        )
    elif settings.embedding_device == "mps":
        console.print("  [yellow]⚠[/yellow] MPS (Apple Silicon) device configured")
        warnings.append(
            ("embedding", "MPS device configured - ensure running on Apple Silicon Mac")
        )


def _validate_llm_model(
    settings: Settings,
    issues: List[Tuple[str, str, str]],
    warnings: List[Tuple[str, str]],
    verbose: bool,
) -> None:
    """Validate LLM model configuration."""
    console.print(f"  [green]✓[/green] LLM model: {settings.llm_model}")

    if verbose:
        console.print(f"    Temperature: {settings.llm_temperature}")
        console.print(f"    Max tokens: {settings.llm_max_tokens}")
        console.print(f"    Context window: {settings.llm_context_window}")

    # Validate temperature
    if not 0.0 <= settings.llm_temperature <= 2.0:
        console.print(f"  [yellow]⚠[/yellow] Unusual temperature: {settings.llm_temperature}")
        warnings.append(
            ("llm", f"Temperature {settings.llm_temperature} is outside typical range (0.0-2.0)")
        )

    # Validate max tokens
    if settings.llm_max_tokens > settings.llm_context_window:
        console.print("  [red]✗[/red] Max tokens exceeds context window")
        issues.append(
            ("ERROR", "llm", f"llm_max_tokens ({settings.llm_max_tokens}) > llm_context_window ({settings.llm_context_window})")
        )


# Import os for directory checks
import os
