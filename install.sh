#!/usr/bin/env bash
# Quick installation script for Ghostline Signal

set -e

echo "==================================="
echo "Ghostline Signal - Installation"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
else
    echo "WARNING: No virtual environment detected."
    echo "It's recommended to use a virtual environment."
    echo ""
    echo "To create one:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
echo ""
echo "To run Ghostline Signal:"
echo "  cd '$SCRIPT_DIR'"
echo "  python3 main.py"
echo ""
echo "For usage instructions, see USAGE.md"
echo ""
