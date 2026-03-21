#!/bin/bash

# ClearClaim Local Demo Runner

echo "=========================================="
echo " Starting ClearClaim Local Demo Environment "
echo "=========================================="

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️ WARNING: ANTHROPIC_API_KEY environment variable is not set."
    echo "The AI Chat Panel will not function correctly without it."
    echo "To set it: export ANTHROPIC_API_KEY='your-key-here'"
    echo "=========================================="
    sleep 2
fi

# Start Backend
echo "Starting FastAPI Backend on port 8000..."
cd clearclaim-backend
pipenv run uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting React Frontend on port 5173..."
cd clearclaim-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "=========================================="
echo "✅ Both servers are starting in the background."
echo ""
echo "🚀 Open the Frontend at: http://localhost:5173"
echo "🔌 Backend API is at:    http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT
wait
