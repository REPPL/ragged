"""Gradio UI launcher."""

from src.web.gradio.ui import create_ui


def launch(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False
) -> None:
    """Launch Gradio UI.

    Args:
        server_name: Host to bind to
        server_port: Port to run on
        share: Whether to create public share link
    """
    app = create_ui()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    launch()
