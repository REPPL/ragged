#!/usr/bin/env bash
# Start the FastAPI server for ragged v0.2

set -e

echo "🚀 Starting ragged API server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs will be at: http://localhost:8000/docs"
echo ""

# Activate virtual environment
source .venv-v0.2/bin/activate

# Start uvicorn server
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --reload
