#!/bin/bash
# VDock Easy Installer for macOS/Linux
# This script will set up VDock automatically

echo "========================================"
echo "   VDock Installation Wizard"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed!${NC}"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}✓ Python found${NC}"

# Check if Node.js is installed
echo "[2/6] Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js is not installed!${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Create Python virtual environment
echo "[3/6] Creating Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    cd backend
    python3 -m venv venv
    cd ..
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Install Python dependencies
echo "[4/6] Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install Python dependencies${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Install frontend dependencies
echo "[5/6] Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install Node.js dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
fi
cd ..

# Create data directories
echo "[6/6] Setting up data directories..."
mkdir -p backend/data/profiles
mkdir -p backend/data/uploads
echo -e "${GREEN}✓ Data directories created${NC}"

# Make launch script executable
chmod +x launch.sh

# Create desktop launcher for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "Creating desktop launcher..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Create app bundle
    cat > ~/Desktop/VDock.command << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
./launch.sh
EOF

    chmod +x ~/Desktop/VDock.command
    echo -e "${GREEN}✓ Desktop launcher created: VDock.command${NC}"
fi

echo ""
echo "========================================"
echo "   Installation Complete!"
echo "========================================"
echo ""
echo "VDock has been installed successfully!"
echo ""
echo "To start VDock:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  1. Double-click 'VDock.command' on your desktop"
else
    echo "  1. Run: ./launch.sh"
fi
echo "  2. Or run: ./launch.sh"
echo ""
echo "Default login: admin / admin"
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo ""
read -p "Would you like to start VDock now? (y/n) " START_NOW

if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting VDock..."
    ./launch.sh
else
    echo ""
    echo "You can start VDock anytime by running: ./launch.sh"
fi

echo ""
