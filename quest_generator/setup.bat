@echo off
REM 🚀 ONE-CLICK QUEST GENERATOR SETUP - WINDOWS
REM Complete automated setup for Cyberpunk Quest Generator

echo 🚀 CYBERPUNK QUEST GENERATOR - ONE-CLICK SETUP
echo ==============================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo 🐍 Python version: %PYTHON_VERSION%

REM Check GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ⚠️ No NVIDIA GPU detected - CPU mode only
) else (
    echo 🎮 NVIDIA GPU detected:
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
python -m pip install requests PyYAML beautifulsoup4 tqdm colorlog aiofiles

REM Check if Ollama is installed
ollama --version >nul 2>&1
if errorlevel 1 (
    echo 📥 Ollama not found. Downloading...
    echo Please download and install from: https://ollama.ai/download/windows
    echo Press any key after installation is complete...
    pause
)

REM Start Ollama server
echo 🚀 Starting Ollama server...
start /b ollama serve
timeout /t 5 /nobreak >nul

REM Download model
echo.
echo 🤖 Available models:
echo 1. llama3.1:8b (Recommended - 8GB VRAM)
echo 2. llama3.1:70b (Best quality - 40GB+ VRAM)
echo 3. qwen2.5:7b (Alternative - 8GB VRAM)
echo 4. Skip model download
echo.

set /p model_choice="Choose model (1-4): "

if "%model_choice%"=="1" (
    echo 📥 Downloading llama3.1:8b...
    ollama pull llama3.1:8b
) else if "%model_choice%"=="2" (
    echo 📥 Downloading llama3.1:70b...
    ollama pull llama3.1:70b
) else if "%model_choice%"=="3" (
    echo 📥 Downloading qwen2.5:7b...
    ollama pull qwen2.5:7b
) else (
    echo ⏭️ Skipping model download
)

REM Create quest generator structure
echo 🏗️ Setting up quest generator...
mkdir quest_generator\data_sources 2>nul
mkdir quest_generator\llm_engine 2>nul
mkdir quest_generator\generators 2>nul
mkdir quest_generator\output 2>nul

REM Test Ollama connection
echo 🔍 Testing Ollama connection...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama not accessible. Please start manually: ollama serve
    pause
    exit /b 1
) else (
    echo ✅ Ollama is running and accessible
)

REM Show available models
echo 📋 Available models:
ollama list

REM Final instructions
echo.
echo 🎉 SETUP COMPLETED!
echo ==================
echo.
echo 📋 NEXT STEPS:
echo 1. Run quest generator:
echo    python quest_generator\generate_quests.py
echo.
echo 2. Generated quests will be saved to:
echo    lore\quests\main_story\
echo    lore\quests\side_quests\
echo    lore\quests\romance_quests\
echo.
echo 💡 TIPS:
echo • Generation takes ~2-3 hours for all quests
echo • Monitor GPU/CPU usage during generation
echo • Backup existing quests before running
echo.
echo 🤖 MODELS USAGE:
echo • Edit model name in generate_quests.py
echo • Default: llama3.1:8b
echo • For better quality: llama3.1:70b
echo.
echo 🚀 START GENERATION:
echo python quest_generator\generate_quests.py
echo.
pause
