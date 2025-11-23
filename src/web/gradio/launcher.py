"""Gradio UI launcher.

v0.5.8: Changed default binding from 0.0.0.0 to 127.0.0.1 for security (MEDIUM-3).
"""

import warnings

from ragged.web.gradio.ui import create_ui


def launch(
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    share: bool = False
) -> None:
    """Launch Gradio UI.

    Args:
        server_name: Host to bind to (default: 127.0.0.1 for security)
        server_port: Port to run on
        share: Whether to create public share link

    Security: v0.5.8 changed default from 0.0.0.0 to 127.0.0.1 to prevent
    accidental network exposure (MEDIUM-3).
    """
    # v0.5.8 MEDIUM-4: Warn about external network exposure
    if server_name == "0.0.0.0":
        warnings.warn(
            "Gradio UI is accessible from external network (0.0.0.0). "
            "Ensure proper authentication and firewall rules are configured.",
            UserWarning,
            stacklevel=2
        )

    app = create_ui()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    launch()
