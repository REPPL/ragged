"""Document upload functionality for Gradio UI."""

from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]

from src.config.constants import LONG_API_TIMEOUT
from src.web.gradio.api import API_UPLOAD


def upload_document(file: Any) -> str:
    """Upload a document to the API.

    Args:
        file: Gradio file upload object

    Returns:
        Status message
    """
    if file is None:
        return "❌ No file selected"

    try:
        # Read file
        file_path = Path(file.name)

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(API_UPLOAD, files=files, timeout=LONG_API_TIMEOUT)
            response.raise_for_status()

        data = response.json()
        status = data.get("status", "unknown")
        message = data.get("message", "")

        if status == "success":
            return f"✅ {message}"
        else:
            return f"⚠️ {message}"

    except Exception as e:  # noqa: BLE001 - Show error to user
        return f"❌ Upload failed: {str(e)}"
