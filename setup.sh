#!/bin/bash

# Setup script for Sales Agent project
# Run this after cloning the repository

echo "================================================"
echo "  Sales Agent Setup Script"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1)
echo "Found: $python_version"

if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found"
echo ""

# Check if .env exists
echo "Checking for .env file..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your FMCSA_API_KEY"
    echo "   nano .env"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your FMCSA_API_KEY:"
echo "   nano .env"
echo ""
echo "2. Start the API:"
echo "   python -m uvicorn app.main:app --reload"
echo ""
echo "3. In a new terminal, start the dashboard:"
echo "   streamlit run streamlit/dashboard.py"
echo ""
echo "4. Run the test script:"
echo "   python tests/populate_test_data.py"
echo ""
echo "5. Open the dashboard:"
echo "   http://localhost:8501"
echo ""
echo "For detailed testing instructions, see:"
echo "   TESTING.md"
echo ""
