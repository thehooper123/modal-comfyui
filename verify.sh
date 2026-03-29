#!/bin/bash
# FitSweetTreat - Pre-Launch Verification Script
# Run this to verify everything is set up before launching the app

echo "🔍 FitSweetTreat Video Automation - Pre-Launch Verification"
echo "============================================================"
echo ""

PASS=0
FAIL=0
WARN=0

# Check Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "   ✅ Python $PY_VERSION found"
    PASS=$((PASS + 1))
else
    echo "   ❌ Python3 not found! Install Python 3.9+"
    FAIL=$((FAIL + 1))
fi

# Check required files
echo ""
echo "2️⃣  Checking required files..."
FILES=("app.py" "callback_server.py" "n8n_workflow_with_callback.json" "requirements.txt" ".env.example")
for FILE in "${FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "   ✅ $FILE"
        PASS=$((PASS + 1))
    else
        echo "   ❌ $FILE missing!"
        FAIL=$((FAIL + 1))
    fi
done

# Check .env
echo ""
echo "3️⃣  Checking .env configuration..."
if [ -f ".env" ]; then
    # Check if .env has content beyond empty template
    if grep -q "your_" .env; then
        echo "   ⚠️  .env exists but contains placeholders"
        echo "      ⚠️  Edit .env with your actual API keys:"
        grep "your_" .env | head -3
        WARN=$((WARN + 1))
    else
        # Check specific variables
        if grep -q "GEMINI_API_KEY" .env && ! grep -q "^GEMINI_API_KEY=$" .env; then
            echo "   ✅ .env configured (at least partially)"
            PASS=$((PASS + 1))
        else
            echo "   ⚠️  .env exists but may not be properly configured"
            WARN=$((WARN + 1))
        fi
    fi
else
    echo "   ⚠️  .env not found"
    echo "      Create it: cp .env.example .env"
    echo "      Then edit with your API keys"
    WARN=$((WARN + 1))
fi

# Check venv
echo ""
echo "4️⃣  Checking Python dependencies..."
if [ -d ".venv" ]; then
    echo "   ✅ Virtual environment exists (.venv/)"
    
    # Check if required packages installed
    source .venv/bin/activate 2>/dev/null
    for PKG in "flask" "requests" "cryptography" "google" "tkinter"; do
        python3 -c "import ${PKG}" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "   ✅ $PKG installed"
            PASS=$((PASS + 1))
        else
            echo "   ⚠️  $PKG may not be installed"
            WARN=$((WARN + 1))
        fi
    done
else
    echo "   ⚠️  Virtual environment not created"
    echo "      Run: python3 -m venv .venv"
    WARN=$((WARN + 1))
fi

# Check documentation
echo ""
echo "5️⃣  Checking documentation..."
DOCS=("SETUP_GUIDE.md" "README_APP.md" "QUICK_REFERENCE.md" "IMPLEMENTATION_SUMMARY.md")
for DOC in "${DOCS[@]}"; do
    if [ -f "$DOC" ]; then
        SIZE=$(wc -l < "$DOC")
        echo "   ✅ $DOC ($SIZE lines)"
        PASS=$((PASS + 1))
    else
        echo "   ⚠️  $DOC missing"
        WARN=$((WARN + 1))
    fi
done

# Check launchers
echo ""
echo "6️⃣  Checking launcher scripts..."
if [ -f "start.sh" ]; then
    echo "   ✅ start.sh (Linux/Mac launcher)"
    PASS=$((PASS + 1))
else
    echo "   ⚠️  start.sh missing"
    WARN=$((WARN + 1))
fi

if [ -f "start.bat" ]; then
    echo "   ✅ start.bat (Windows launcher)"
    PASS=$((PASS + 1))
else
    echo "   ⚠️  start.bat missing"
    WARN=$((WARN + 1))
fi

# Check external services
echo ""
echo "7️⃣  Checking external services (required but not running)..."
echo "   ℹ️  These need to be running in separate terminals:"

echo -n "   • n8n (localhost:5678): "
curl -s http://localhost:5678/api/v1/health &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Running"
    PASS=$((PASS + 1))
else
    echo "❌ Not running (start it separately)"
    FAIL=$((FAIL + 1))
fi

echo -n "   • KokoroTTS (localhost:8000): "
curl -s http://localhost:8000/health &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Running"
    PASS=$((PASS + 1))
else
    echo "❌ Not running (start it separately)"
    FAIL=$((FAIL + 1))
fi

# Summary
echo ""
echo "============================================================"
echo "📊 VERIFICATION SUMMARY"
echo "============================================================"
echo "✅ Passed:  $PASS"
echo "⚠️  Warnings: $WARN"
echo "❌ Failed:  $FAIL"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -le 2 ]; then
    echo "🎉 All systems ready! You can launch the app."
    echo ""
    echo "Next steps:"
    echo "  1. Make sure n8n is running: docker run -p 5678:5678 n8nio/n8n"
    echo "  2. Make sure KokoroTTS is running: docker run -p 8000:8000 kokoro-tts"
    echo "  3. Import n8n workflow: n8n_workflow_with_callback.json"
    echo "  4. Run the app: python app.py"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo "⚠️  Some warnings detected. Review above."
    echo ""
    echo "Most critical:"
    echo "  • Edit .env with your API keys"
    echo "  • Ensure n8n and KokoroTTS are running"
    exit 0
else
    echo "❌ Critical issues detected. Please fix above."
    exit 1
fi
