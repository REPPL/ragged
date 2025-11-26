"""
Success Screen.

WIZARD-001: Final screen showing installation success and next steps.
"""

from rich.markdown import Markdown
from rich.panel import Panel

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


class SuccessScreen(WizardScreen):
    """Final success screen."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Installation Complete"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "ragged is ready to use"

    def render(self) -> None:
        """Render success message."""
        config = self.wizard.get_choice("config", {})
        verification_passed = self.wizard.get_choice("verification_passed", True)

        if verification_passed:
            self._render_success(config)
        else:
            self._render_partial_success(config)

    def _render_success(self, config: dict) -> None:
        """Render full success message."""
        ragged_home = config.get("ragged_home", "~/.ragged")
        api_port = config.get("api_port", "8000")
        webui_port = config.get("webui_port", "5173")

        success_text = f"""
# Congratulations!

ragged has been successfully installed and configured.

## Quick Start

**Start the services:**
```bash
ragged start
```

**Access the web interface:**
Open http://localhost:{webui_port} in your browser.

**Add documents:**
```bash
ragged add /path/to/documents
```

**Ask questions:**
```bash
ragged ask "What is this document about?"
```

## Configuration

Your ragged installation is located at:
```
{ragged_home}
```

## Getting Help

- Run `ragged --help` for command reference
- Check the documentation at https://github.com/ragged/ragged
- Report issues at https://github.com/ragged/ragged/issues

## Next Steps

1. Start ragged with `ragged start`
2. Open the web interface
3. Add your first documents
4. Start asking questions!
"""

        self.console.print(Markdown(success_text))

    def _render_partial_success(self, config: dict) -> None:
        """Render partial success with issues."""
        self.console.print(
            Panel(
                "[yellow]Installation completed with some issues.[/yellow]\n\n"
                "ragged is installed but some verification checks failed.\n"
                "You may need to complete setup manually.",
                border_style="yellow",
            )
        )
        self.console.print()

        # Show what worked
        setup_results = self.wizard.get_result("setup_results", {})
        successful = [k for k, v in setup_results.items() if v.get("success")]
        failed = [k for k, v in setup_results.items() if not v.get("success")]

        if successful:
            self.console.print("[bold]Completed:[/bold]")
            for item in successful:
                self.console.print(f"  [green]Checkmark[/green] {item.title()}")
            self.console.print()

        if failed:
            self.console.print("[bold]Needs attention:[/bold]")
            for item in failed:
                result = setup_results.get(item, {})
                self.console.print(f"  [red]X[/red] {item.title()}: {result.get('message', '')}")
            self.console.print()

        # Show manual steps
        manual_steps = f"""
## Manual Steps

If you encountered issues, try these steps:

1. **Start Docker** (if using Docker ChromaDB):
   ```bash
   docker compose -f {config.get('ragged_home', '~/.ragged')}/docker-compose.yml up -d
   ```

2. **Pull the LLM model**:
   ```bash
   ollama pull {config.get('llm_model', 'llama3.2')}
   ```

3. **Start ragged**:
   ```bash
   ragged start
   ```

For help, run `ragged doctor` to diagnose issues.
"""
        self.console.print(Markdown(manual_steps))

    def process(self) -> NavigationAction:
        """Process - this is the final screen."""
        from rich.prompt import Prompt

        self.console.print()
        Prompt.ask("[dim]Press Enter to finish[/dim]", default="")

        return NavigationAction.NEXT
