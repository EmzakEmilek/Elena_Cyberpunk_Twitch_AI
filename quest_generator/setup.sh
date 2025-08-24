#!/usr/bin/env bash
# 🚀 ONE-CLICK QUEST GENERATOR SETUP
# Complete automated setup for Cyberpunk Quest Generator

echo "🚀 CYBERPUNK QUEST GENERATOR - ONE-CLICK SETUP"
echo "=============================================="

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

OS=$(detect_os)
echo "🖥️ Detected OS: $OS"

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python version: $PYTHON_VERSION"

# Check GPU (NVIDIA)
if command_exists nvidia-smi; then
    echo "🎮 NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️ No NVIDIA GPU detected - CPU mode only"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install requests PyYAML beautifulsoup4 tqdm colorlog aiofiles

# Install Ollama based on OS
echo "🔽 Installing Ollama..."

if [[ "$OS" == "linux" ]]; then
    curl -fsSL https://ollama.ai/install.sh | sh
elif [[ "$OS" == "macos" ]]; then
    if command_exists brew; then
        brew install ollama
    else
        echo "📥 Please download Ollama from: https://ollama.ai/download/mac"
        read -p "Press Enter after installing Ollama..."
    fi
elif [[ "$OS" == "windows" ]]; then
    echo "📥 Please download and install Ollama from: https://ollama.ai/download/windows"
    read -p "Press Enter after installing Ollama..."
fi

# Start Ollama server
echo "🚀 Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# Download model
echo "🤖 Available models:"
echo "1. llama3.1:8b (Recommended - 8GB VRAM)"
echo "2. llama3.1:70b (Best quality - 40GB+ VRAM)"
echo "3. qwen2.5:7b (Alternative - 8GB VRAM)"
echo "4. Skip model download"

read -p "Choose model (1-4): " model_choice

case $model_choice in
    1)
        echo "📥 Downloading llama3.1:8b..."
        ollama pull llama3.1:8b
        ;;
    2)
        echo "📥 Downloading llama3.1:70b..."
        ollama pull llama3.1:70b
        ;;
    3)
        echo "📥 Downloading qwen2.5:7b..."
        ollama pull qwen2.5:7b
        ;;
    4)
        echo "⏭️ Skipping model download"
        ;;
    *)
        echo "⏭️ Invalid choice, skipping model download"
        ;;
esac

# Create quest generator structure
echo "🏗️ Setting up quest generator..."
mkdir -p quest_generator/{data_sources,llm_engine,generators,output}

# Test Ollama connection
echo "🔍 Testing Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running and accessible"
else
    echo "❌ Ollama not accessible. Please start manually: ollama serve"
    exit 1
fi

# Show available models
echo "📋 Available models:"
ollama list

# Final instructions
echo ""
echo "🎉 SETUP COMPLETED!"
echo "=================="
echo ""
echo "📋 NEXT STEPS:"
echo "1. Run quest generator:"
echo "   python3 quest_generator/generate_quests.py"
echo ""
echo "2. Generated quests will be saved to:"
echo "   lore/quests/main_story/"
echo "   lore/quests/side_quests/"
echo "   lore/quests/romance_quests/"
echo ""
echo "💡 TIPS:"
echo "• Generation takes ~2-3 hours for all quests"
echo "• Monitor GPU/CPU usage during generation"
echo "• Backup existing quests before running"
echo ""
echo "🤖 MODELS USAGE:"
echo "• Edit model name in generate_quests.py"
echo "• Default: llama3.1:8b"
echo "• For better quality: llama3.1:70b"
echo ""
echo "🚀 START GENERATION:"
echo "python3 quest_generator/generate_quests.py"
