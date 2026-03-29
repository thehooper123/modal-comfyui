#!/bin/bash
# FitSweetTreat Video Automation - Startup Script
# Starts all required services for the video automation pipeline

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📦 Starting FitSweetTreat Video Automation Pipeline"
echo "🏗️  Project Directory: $PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Python
echo -e "${BLUE}[1/5]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found!${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Setup venv
echo -e "${BLUE}[2/5]${NC} Setting up virtual environment..."
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    python3 -m venv .venv
fi
source "$PROJECT_DIR/.venv/bin/activate"
pip install --upgrade pip -q
echo -e "${GREEN}✓ Virtual environment ready${NC}"

# Install dependencies
echo -e "${BLUE}[3/5]${NC} Installing dependencies..."
pip install -q -r "$PROJECT_DIR/requirements.txt" || {
    echo -e "${YELLOW}⚠️  Some packages may require manual installation${NC}"
}
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check required services
echo -e "${BLUE}[4/5]${NC} Checking required services..."
echo ""
echo -e "${YELLOW}Required Services:${NC}"
echo -e "  • ${BLUE}n8n${NC}: http://localhost:5678 (not auto-started)"
echo -e "  • ${BLUE}KokoroTTS${NC}: http://localhost:8000 (not auto-started)"
echo -e "  • ${BLUE}Gemini API${NC}: Requires .env credentials"
echo ""

# Check .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo "Creating from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}📝 Please edit .env with your credentials:${NC}"
    echo "   nano .env"
    echo ""
fi

# Start services
echo -e "${BLUE}[5/5]${NC} Starting services..."
echo ""

# Start callback server
echo -e "${GREEN}➤ Starting Callback Server (port 5000)${NC}"
python "$PROJECT_DIR/callback_server.py" &
CALLBACK_PID=$!
sleep 2
echo -e "${GREEN}✓ Callback Server started (PID: $CALLBACK_PID)${NC}"

# Start main app
echo ""
echo -e "${GREEN}➤ Starting FitSweetTreat App${NC}"
python "$PROJECT_DIR/app.py" &
APP_PID=$!
echo -e "${GREEN}✓ App started (PID: $APP_PID)${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ FitSweetTreat Video Automation Pipeline Ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📋 Services Running:${NC}"
echo -e "  • Callback Server: http://localhost:5000"
echo -e "  • Main App UI: Tkinter window (just opened)"
echo ""
echo -e "${YELLOW}⚠️  Make sure these services are also running:${NC}"
echo "  1. n8n: http://localhost:5678"
echo "  2. KokoroTTS: http://localhost:8000"
echo ""
echo -e "${YELLOW}📁 Key Files:${NC}"
echo "  • app.py - Main application (running)"
echo -e "  • callback_server.py - Video delivery server (running)"
echo "  • n8n_workflow_with_callback.json - n8n workflow to import"
echo "  • SETUP_GUIDE.md - Complete documentation"
echo ".env - Your API credentials (EDIT THIS!)"
echo ""
echo -e "${YELLOW}🎬 Next Steps:${NC}"
echo "  1. Edit .env with your API keys"
echo "  2. Ensure n8n is running: http://localhost:5678"
echo "  3. Ensure KokoroTTS is running: http://localhost:8000"
echo "  4. Import n8n_workflow_with_callback.json into n8n"
echo "  5. Test with a recipe prompt in the App!"
echo ""

# Wait for user interrupt
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
wait

echo -e "${GREEN}✓ Shutting down...${NC}"
kill $CALLBACK_PID $APP_PID 2>/dev/null || true
