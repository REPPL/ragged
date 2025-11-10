#!/usr/bin/env bash
# Start both the API server and Gradio UI for ragged v0.2

set -e

echo "🚀 Starting ragged v0.2..."
echo ""
echo "📍 API server: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🎨 Gradio UI: http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Activate virtual environment
source .venv-v0.2/bin/activate

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $API_PID $UI_PID 2>/dev/null
    wait $API_PID $UI_PID 2>/dev/null
    echo "✅ Servers stopped"
}

trap cleanup EXIT INT TERM

# Start API server in background
echo "Starting API server..."
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to be ready..."
sleep 3

# Start Gradio UI in background
echo "Starting Gradio UI..."
python -m src.web.gradio_ui &
UI_PID=$!

# Wait for both processes
echo ""
echo "✅ Both servers running!"
echo "   API: http://localhost:8000"
echo "   UI:  http://localhost:7860"
echo ""
wait
