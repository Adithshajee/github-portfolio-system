#!/usr/bin/env bash
# ==============================================================================
# GPS Developer Identity Platform Bootstrapping Setup Script (Unix/macOS)
# ==============================================================================
set -e

echo "============================================================================"
echo "🚀 GPS Bootstrapping Setup Workspace Automation"
echo "============================================================================"

# 1. Verify Python
echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed or not in PATH. Please install Python 3.10+"
    exit 1
fi
pyver=$(python3 --version | cut -d' ' -f2)
echo "✓ Python version: $pyver"

# 2. Verify Git
echo "Checking Git..."
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git."
    exit 1
fi
echo "✓ Git detected."

# 3. Verify pip
echo "Checking pip..."
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is not installed. Enable pip."
    exit 1
fi
echo "✓ pip detected."

# 4. Verify Internet
echo "Checking internet connection..."
if ! ping -c 1 pypi.org &> /dev/null; then
    # Fallback check using curl
    if ! curl -I https://pypi.org &> /dev/null; then
        echo "❌ Internet connection is offline. Setup requires online packages access."
        exit 1
    fi
fi
echo "✓ Internet connectivity verified."

# 5. Verify Write Permissions
echo "Checking folder write permissions..."
if ! touch write_test.tmp &> /dev/null; then
    echo "❌ Write permissions check failed. Run setup in a writable folder."
    exit 1
fi
rm write_test.tmp
echo "✓ Write permissions verified."

# 6. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi
echo "✓ Virtual environment ready."

# 7. Activate venv & Install package
echo "Activating .venv and installing GPS dependencies..."
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,huggingface,kaggle]"
echo "✓ Installation completed."

# 8. Generate configuration gps.yml if missing
if [ ! -f "gps.yml" ]; then
    echo "Generating default gps.yml..."
    gps init --non-interactive --force
else
    echo "✓ gps.yml already exists."
fi

# 9. Generate folders and files scaffolding
mkdir -p profile
if [ ! -f "profile/README.md" ]; then
    echo "Creating default profile README.md..."
    echo "# Developer Profile" > profile/README.md
    echo "" >> profile/README.md
    echo "<!-- REPOS_START -->" >> profile/README.md
    echo "<!-- REPOS_END -->" >> profile/README.md
fi
echo "✓ Scaffolding files ready."

# 10. Run validation pipeline
echo "Running system diagnostics checks..."
if ! gps doctor; then
    echo "⚠️ Health checks reported warnings."
elif ! gps verify; then
    echo "⚠️ Health checks reported warnings."
else
    echo "✓ All system checks passed successfully."
fi

echo ""
echo "============================================================================"
echo "🎉 GPS Developer Identity Platform Setup successfully completed!"
echo "============================================================================"
echo ""
echo "Next Steps:"
echo "  1. Activate virtual environment:  source .venv/bin/activate"
echo "  2. Run visual dashboard:          gps dashboard"
echo "  3. Launch preview:                http://localhost:8080"
echo ""
exit 0
