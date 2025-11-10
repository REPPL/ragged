#!/usr/bin/env bash
# Start the Gradio web UI for ragged v0.2

set -e

echo "🎨 Starting ragged Gradio UI..."
echo "📍 UI will be available at: http://localhost:7860"
echo ""
echo "⚠️  Make sure the API server is running first!"
echo "   Run: ./scripts/start_api.sh"
echo ""

# Activate virtual environment
source .venv-v0.2/bin/activate

# Start Gradio UI
python -m src.web.gradio_ui
