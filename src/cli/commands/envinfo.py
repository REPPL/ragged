"""Environment information command for ragged CLI.

Displays system and environment information for bug reports and troubleshooting.
"""

import platform
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from src import __version__
from src.cli.common import click, console
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command(name="env-info")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    help="Output format",
)
@click.option(
    "--copy",
    "-c",
    is_flag=True,
    help="Copy output to clipboard (requires pyperclip)",
)
def env_info(format: str, copy: bool) -> None:
    """Show environment information for bug reports.

    Displays system information, Python version, installed packages,
    and ragged configuration for debugging and support.

    \b
    Examples:
        # Show environment info
        ragged env-info

        # Export as JSON
        ragged env-info --format json

        # Generate markdown for GitHub issues
        ragged env-info --format markdown

        # Copy to clipboard
        ragged env-info --copy
    """
    info = _gather_environment_info()

    if format == "json":
        output = _format_json(info)
    elif format == "markdown":
        output = _format_markdown(info)
    else:  # text
        output = _format_text(info)

    if copy:
        try:
            import pyperclip

            pyperclip.copy(output)
            console.print("[green]✓[/green] Environment info copied to clipboard")
        except ImportError:
            console.print(
                "[yellow]⚠[/yellow] pyperclip not installed. Install with: pip install pyperclip"
            )
            console.print("\n" + output)
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not copy to clipboard: {e}")
            console.print("\n" + output)
    else:
        console.print(output)


def _gather_environment_info() -> Dict[str, Any]:
    """Gather all environment information."""
    info: Dict[str, Any] = {}

    # Ragged version
    info["ragged_version"] = __version__

    # Python information
    info["python"] = {
        "version": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "executable": sys.executable,
    }

    # System information
    info["system"] = {
        "os": platform.system(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "Unknown",
    }

    # Package versions
    info["packages"] = _get_package_versions()

    # Configuration (non-sensitive)
    try:
        settings = get_settings()
        info["config"] = {
            "embedding_model": settings.embedding_model,
            "embedding_model_name": settings.embedding_model_name,
            "embedding_device": settings.embedding_device,
            "llm_model": settings.llm_model,
            "ollama_base_url": settings.ollama_base_url,
            "chroma_collection_name": settings.chroma_collection_name,
            "chunking_strategy": settings.chunking_strategy,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
        }
    except Exception as e:
        info["config"] = {"error": str(e)}

    # Ollama status
    info["ollama"] = _check_ollama_status()

    # Disk space
    info["storage"] = _check_storage()

    return info


def _get_package_versions() -> Dict[str, str]:
    """Get versions of key installed packages."""
    packages = {}
    key_packages = [
        "click",
        "rich",
        "pydantic",
        "chromadb",
        "sentence-transformers",
        "ollama",
        "fastapi",
        "gradio",
        "httpx",
        "torch",
        "transformers",
    ]

    for package in key_packages:
        try:
            import importlib.metadata

            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "Not installed"
        except Exception:
            packages[package] = "Unknown"

    return packages


def _check_ollama_status() -> Dict[str, Any]:
    """Check Ollama service status."""
    try:
        settings = get_settings()
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name", "unknown") for m in data.get("models", [])]
            return {
                "status": "running",
                "url": settings.ollama_base_url,
                "models_count": len(models),
                "models": models[:5],  # First 5 models
            }
        else:
            return {
                "status": f"error (HTTP {response.status_code})",
                "url": settings.ollama_base_url,
            }
    except httpx.ConnectError:
        return {"status": "not reachable", "url": settings.ollama_base_url}
    except Exception as e:
        return {"status": f"error: {e}"}


def _check_storage() -> Dict[str, Any]:
    """Check storage space for data directories."""
    import shutil

    storage = {}

    try:
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        if data_dir.exists():
            stat = shutil.disk_usage(data_dir)
            storage["data_directory"] = {
                "path": str(data_dir),
                "total_gb": round(stat.total / (1024**3), 2),
                "used_gb": round(stat.used / (1024**3), 2),
                "free_gb": round(stat.free / (1024**3), 2),
                "percent_used": round((stat.used / stat.total) * 100, 1),
            }
        else:
            storage["data_directory"] = {"path": str(data_dir), "status": "does not exist"}

    except Exception as e:
        storage["error"] = str(e)

    return storage


def _format_text(info: Dict[str, Any]) -> str:
    """Format information as plain text."""
    lines = []

    lines.append("=" * 60)
    lines.append("Ragged Environment Information")
    lines.append("=" * 60)
    lines.append("")

    # Version
    lines.append(f"Ragged Version: {info['ragged_version']}")
    lines.append("")

    # Python
    lines.append("Python:")
    lines.append(f"  Version: {info['python']['version']}")
    lines.append(f"  Implementation: {info['python']['implementation']}")
    lines.append(f"  Executable: {info['python']['executable']}")
    lines.append("")

    # System
    lines.append("System:")
    lines.append(f"  OS: {info['system']['os']}")
    lines.append(f"  Platform: {info['system']['platform']}")
    lines.append(f"  Machine: {info['system']['machine']}")
    lines.append(f"  Processor: {info['system']['processor']}")
    lines.append("")

    # Packages
    lines.append("Key Packages:")
    for pkg, version in sorted(info["packages"].items()):
        lines.append(f"  {pkg}: {version}")
    lines.append("")

    # Configuration
    lines.append("Configuration:")
    if "error" in info["config"]:
        lines.append(f"  Error: {info['config']['error']}")
    else:
        for key, value in sorted(info["config"].items()):
            lines.append(f"  {key}: {value}")
    lines.append("")

    # Ollama
    lines.append("Ollama:")
    if "status" in info["ollama"]:
        lines.append(f"  Status: {info['ollama']['status']}")
        if "url" in info["ollama"]:
            lines.append(f"  URL: {info['ollama']['url']}")
        if "models_count" in info["ollama"]:
            lines.append(f"  Models: {info['ollama']['models_count']}")
            if info["ollama"].get("models"):
                for model in info["ollama"]["models"]:
                    lines.append(f"    - {model}")
    lines.append("")

    # Storage
    lines.append("Storage:")
    if "data_directory" in info["storage"]:
        dd = info["storage"]["data_directory"]
        lines.append(f"  Data Directory: {dd.get('path', 'Unknown')}")
        if "free_gb" in dd:
            lines.append(
                f"  Space: {dd['free_gb']}GB free / {dd['total_gb']}GB total ({dd['percent_used']}% used)"
            )
        elif "status" in dd:
            lines.append(f"  Status: {dd['status']}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def _format_json(info: Dict[str, Any]) -> str:
    """Format information as JSON."""
    import json

    return json.dumps(info, indent=2)


def _format_markdown(info: Dict[str, Any]) -> str:
    """Format information as Markdown for GitHub issues."""
    lines = []

    lines.append("## Environment Information")
    lines.append("")
    lines.append(f"**Ragged Version:** {info['ragged_version']}")
    lines.append("")

    lines.append("### Python")
    lines.append(f"- **Version:** {info['python']['version']}")
    lines.append(f"- **Implementation:** {info['python']['implementation']}")
    lines.append("")

    lines.append("### System")
    lines.append(f"- **OS:** {info['system']['os']}")
    lines.append(f"- **Platform:** {info['system']['platform']}")
    lines.append(f"- **Machine:** {info['system']['machine']}")
    lines.append("")

    lines.append("### Key Packages")
    lines.append("```")
    for pkg, version in sorted(info["packages"].items()):
        lines.append(f"{pkg}: {version}")
    lines.append("```")
    lines.append("")

    lines.append("### Configuration")
    if "error" in info["config"]:
        lines.append(f"**Error:** {info['config']['error']}")
    else:
        lines.append("```yaml")
        for key, value in sorted(info["config"].items()):
            lines.append(f"{key}: {value}")
        lines.append("```")
    lines.append("")

    lines.append("### Ollama Status")
    if "status" in info["ollama"]:
        lines.append(f"- **Status:** {info['ollama']['status']}")
        if "models_count" in info["ollama"]:
            lines.append(f"- **Models:** {info['ollama']['models_count']}")

    lines.append("")
    lines.append("---")
    lines.append("*Generated with `ragged env-info --format markdown`*")

    return "\n".join(lines)
