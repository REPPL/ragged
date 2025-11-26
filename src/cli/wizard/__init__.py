"""
Installation Wizard.

WIZARD-001: Interactive CLI wizard for guided ragged installation.
Uses rich library for beautiful terminal UI.
"""

from ragged.cli.wizard.framework import (
    Wizard,
    WizardScreen,
    WizardState,
    NavigationAction,
)
from ragged.cli.wizard.runner import run_installation_wizard


__all__ = [
    "Wizard",
    "WizardScreen",
    "WizardState",
    "NavigationAction",
    "run_installation_wizard",
]
