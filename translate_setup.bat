@echo off
chcp 65001 >nul
echo 🌍 SLOVAKIA CARD TRANSLATOR - SETUP
echo =====================================

echo.
echo 📋 1. Kontrolujem Python environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Python environment sa nenašiel!
    echo 💡 Spusti najprv: python -m venv .venv
    pause
    exit /b 1
)

echo ✅ Python environment aktívny

echo.
echo 📦 2. Inštalujem dependencies...
pip install requests pyyaml colorlog tqdm
if errorlevel 1 (
    echo ❌ Inštalácia zlyhala!
    pause
    exit /b 1
)

echo ✅ Dependencies nainštalované

echo.
echo 🔄 3. Kontrolujem Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama nie je spustená!
    echo.
    echo 💡 SPUSTI V NOVOM TERMINÁLY:
    echo    ollama serve
    echo.
    echo 💡 POTOM STIAHNI MODEL:
    echo    ollama pull llama3.1:8b
    echo.
    pause
    exit /b 1
)

echo ✅ Ollama beží

echo.
echo 🚀 4. Spúšťam preklad...
echo ⏰ Očakávaný čas: 20-30 minút pre 249 kariet
echo.

python quest_generator/translate_cards.py

echo.
echo ✅ HOTOVO! Všetky karty sú preložené do slovenčiny.
pause
