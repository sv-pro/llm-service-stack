#!/bin/bash
set -e

echo "🚀 AI Aikido Gateway - Setup Script"
echo "===================================="
echo ""

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo "❌ pyenv is not installed. Please install pyenv first."
    echo "   Visit: https://github.com/pyenv/pyenv#installation"
    exit 1
fi

echo "✅ pyenv found"

# Check Python version
REQUIRED_PYTHON="3.11"
if ! pyenv versions | grep -q "$REQUIRED_PYTHON"; then
    echo "📦 Installing Python $REQUIRED_PYTHON..."
    pyenv install 3.11.7
else
    echo "✅ Python $REQUIRED_PYTHON already installed"
fi

# Create virtual environment
ENV_NAME="aikido-env"
if ! pyenv virtualenvs | grep -q "$ENV_NAME"; then
    echo "🔧 Creating virtual environment: $ENV_NAME"
    pyenv virtualenv 3.11.7 $ENV_NAME
else
    echo "✅ Virtual environment $ENV_NAME already exists"
fi

# Set local Python version
echo "🔧 Setting local Python version"
pyenv local $ENV_NAME

# Upgrade pip
echo "📦 Upgrading pip, setuptools, and wheel"
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📦 Installing production dependencies"
pip install -r requirements.txt

echo "📦 Installing development dependencies"
pip install -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example"
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✅ .env file already exists"
fi

# Install pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    echo "🔧 Installing pre-commit hooks"
    pre-commit install
else
    echo "⚠️  pre-commit not found, skipping hooks installation"
fi

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python -c "import fastapi; import anthropic; import openai; print('✅ All imports successful')" || {
    echo "❌ Import verification failed"
    exit 1
}

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: uvicorn src.main:app --reload"
echo "3. Visit: http://localhost:8000/docs"
echo ""
