"""
Installation Scripts.

WIZARD-002: One-command installation scripts for ragged.
"""

from ragged.install.scripts.bootstrap import (
    generate_bootstrap_script,
    BootstrapOptions,
)


__all__ = [
    "generate_bootstrap_script",
    "BootstrapOptions",
]
