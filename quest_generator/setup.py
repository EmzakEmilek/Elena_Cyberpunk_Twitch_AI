#!/usr/bin/env python3
"""
🏗️ SETUP SCRIPT FOR QUEST GENERATOR
Automated setup of local LLM quest generation environment
"""

import subprocess
import sys
import platform
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestGeneratorSetup:
    """Setup manager for quest generator"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
    def check_requirements(self):
        """Check system requirements"""
        logger.info("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            return False
        
        # Check available RAM
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
            logger.info(f"💾 Available RAM: {ram_gb:.1f} GB")
            
            if ram_gb < 16:
                logger.warning("⚠️ Recommended: 32GB+ RAM for large models")
        except ImportError:
            logger.info("📊 Install psutil for system monitoring")
        
        # Check GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                for gpu in gpus:
                    logger.info(f"🎮 GPU: {gpu.name} ({gpu.memoryTotal}MB)")
            else:
                logger.warning("⚠️ No GPU detected - CPU mode only")
        except ImportError:
            logger.info("🔧 Install GPUtil for GPU monitoring")
        
        return True
    
    def install_ollama(self):
        """Install Ollama for local LLM"""
        logger.info("🔽 Installing Ollama...")
        
        try:
            # Check if already installed
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Ollama already installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        # Install based on OS
        if self.system == "windows":
            logger.info("📥 Download Ollama from: https://ollama.ai/download/windows")
            logger.info("🔧 Run the installer and restart this script")
            return False
        
        elif self.system == "linux":
            cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            logger.info(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0
        
        elif self.system == "darwin":  # macOS
            logger.info("📥 Download Ollama from: https://ollama.ai/download/mac")
            return False
        
        return False
    
    def download_model(self, model_name: str = "llama3.1:8b"):
        """Download LLM model"""
        logger.info(f"📥 Downloading model: {model_name}")
        
        try:
            # Start Ollama server if not running
            self.start_ollama_server()
            
            # Download model
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Model downloaded: {model_name}")
                return True
            else:
                logger.error(f"❌ Failed to download {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return False
    
    def start_ollama_server(self):
        """Start Ollama server"""
        try:
            # Check if server is already running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("✅ Ollama server already running")
                return True
        except:
            pass
        
        logger.info("🚀 Starting Ollama server...")
        
        if self.system == "windows":
            # On Windows, Ollama typically runs as a service
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # On Unix systems
            subprocess.Popen(["ollama", "serve"])
        
        # Wait for server to start
        import time
        for i in range(10):
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Ollama server started")
                    return True
            except:
                time.sleep(2)
        
        logger.error("❌ Failed to start Ollama server")
        return False
    
    def install_python_deps(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                "quest_generator/requirements.txt"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Python dependencies installed")
                return True
            else:
                logger.error(f"❌ Failed to install dependencies: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def setup_complete(self):
        """Complete setup process"""
        logger.info("🎯 Setup completed!")
        logger.info("\n📋 NEXT STEPS:")
        logger.info("1. Verify Ollama is running: ollama list")
        logger.info("2. Run quest generator: python quest_generator/generate_quests.py")
        logger.info("3. Check generated quests in lore/quests/")
        
        # Show recommended models
        logger.info("\n🤖 RECOMMENDED MODELS:")
        logger.info("• llama3.1:8b (8GB VRAM) - Fast, good quality")
        logger.info("• llama3.1:70b (40GB+ VRAM) - Best quality")
        logger.info("• qwen2.5:72b (45GB+ VRAM) - Best multilingual")
        
        logger.info("\n💡 USAGE:")
        logger.info("ollama pull llama3.1:8b  # Download model")
        logger.info("python quest_generator/generate_quests.py  # Generate quests")

def main():
    """Main setup function"""
    logger.info("🚀 CYBERPUNK QUEST GENERATOR SETUP")
    logger.info("==================================")
    
    setup = QuestGeneratorSetup()
    
    # Check requirements
    if not setup.check_requirements():
        return False
    
    # Install Python dependencies
    if not setup.install_python_deps():
        return False
    
    # Install Ollama
    if not setup.install_ollama():
        logger.warning("⚠️ Please install Ollama manually and restart")
        return False
    
    # Download recommended model
    model_choice = input("\n🤖 Download model? (1=llama3.1:8b, 2=llama3.1:70b, n=skip): ")
    
    if model_choice == "1":
        setup.download_model("llama3.1:8b")
    elif model_choice == "2":
        setup.download_model("llama3.1:70b")
    else:
        logger.info("⏭️ Skipping model download")
    
    # Complete setup
    setup.setup_complete()
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("🎉 Setup completed successfully!")
    else:
        logger.error("❌ Setup failed")
        sys.exit(1)
