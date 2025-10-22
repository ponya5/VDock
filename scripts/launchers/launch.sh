#!/bin/bash
# VDock Launch Script for macOS/Linux

echo "========================================"
echo "   VDock Virtual Stream Deck Launcher"
echo "========================================"
echo ""

# Check virtual environment
echo "[1/5] Checking virtual environment..."
if [ ! -d "backend/venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run install.sh first."
    exit 1
fi
echo "✓ Virtual environment found"

# Check frontend dependencies
echo "[2/5] Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi
echo "✓ Frontend dependencies ready"

# Start backend server
echo "[3/5] Starting Backend Server..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to initialize
echo "[4/5] Waiting for backend to initialize..."
sleep 5

# Start frontend server
echo "[5/5] Starting Frontend Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "   VDock is starting up!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Login: admin / admin"
echo ""
echo "Waiting for servers to be ready..."
sleep 3

# Open browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Opening VDock in your browser..."
    open http://localhost:3000
# Open browser (Linux)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    fi
fi

echo ""
echo "========================================"
echo "   VDock launched successfully!"
echo "========================================"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop VDock:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or press Ctrl+C in each terminal"
echo ""

# Keep script running
wait
