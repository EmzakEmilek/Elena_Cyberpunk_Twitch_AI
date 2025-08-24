# 🤖 CYBERPUNK QUEST GENERATOR - USAGE GUIDE

## 🚀 QUICK START (One Command)

### Windows:
```cmd
quest_generator\setup.bat
```

### Linux/macOS:
```bash
chmod +x quest_generator/setup.sh
./quest_generator/setup.sh
```

## 📋 MANUAL SETUP

### 1. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.ai/download/windows
```

### 2. Start Ollama Server
```bash
ollama serve
```

### 3. Download Model
```bash
# Recommended for most users (8GB VRAM)
ollama pull llama3.1:8b

# Best quality (40GB+ VRAM required)
ollama pull llama3.1:70b

# Alternative multilingual
ollama pull qwen2.5:7b
```

### 4. Install Python Dependencies
```bash
pip install -r quest_generator/requirements.txt
```

### 5. Run Quest Generator
```bash
python quest_generator/generate_quests.py
```

## 🎯 EXPECTED RESULTS

### Before Generation:
```
lore/quests/
├── main_story/     (24 quests)
├── side_quests/    (16 quests) 
└── romance_quests/ (4 quests)
Total: 44 quests
```

### After Generation:
```
lore/quests/
├── main_story/     (~35 quests)
├── side_quests/    (~80 quests)
├── romance_quests/ (~15 quests)
└── gigs/          (~50 quests)
Total: ~180 quests
```

## ⚙️ CONFIGURATION

### Change Model in generate_quests.py:
```python
# Line 73: Choose your model
llm = OllamaClient(model="llama3.1:8b")  # Change this

# Options:
# "llama3.1:8b"     - Fast, 8GB VRAM
# "llama3.1:70b"    - Best quality, 40GB+ VRAM  
# "qwen2.5:7b"      - Alternative, 8GB VRAM
# "qwen2.5:72b"     - Best multilingual, 45GB+ VRAM
```

### Customize Quest Lists:
Edit `missing_quests` array in `generate_quests.py` to add/remove quests.

## 🔧 TROUBLESHOOTING

### Ollama Server Not Starting:
```bash
# Check if running
curl http://localhost:11434/api/tags

# Kill existing process
pkill ollama
ollama serve

# Windows
taskkill /f /im ollama.exe
ollama serve
```

### Out of Memory Errors:
```bash
# Use smaller model
ollama pull llama3.1:8b

# Or reduce context in script
# Edit generate_quests.py line 45:
"max_tokens": 1024  # Reduce from 2048
```

### Slow Generation:
```bash
# Enable GPU acceleration
export OLLAMA_GPU=1

# Use faster model
ollama pull llama3.1:8b
```

### Invalid YAML Output:
The script includes automatic YAML cleaning. If issues persist:
1. Check model quality
2. Verify prompts are working
3. Manually review generated files

## 📊 PERFORMANCE EXPECTATIONS

### Hardware Requirements:
| Model | VRAM | RAM | Speed | Quality |
|-------|------|-----|-------|---------|
| llama3.1:8b | 8GB | 16GB | Fast | Good |
| llama3.1:70b | 40GB | 64GB | Slow | Excellent |
| qwen2.5:7b | 8GB | 16GB | Fast | Good |
| qwen2.5:72b | 45GB | 64GB | Slow | Excellent |

### Generation Time:
- **8B model**: ~2-3 hours for all quests
- **70B model**: ~8-12 hours for all quests
- **Rate limiting**: 2 seconds between requests

### Cost Comparison:
- **Local LLM**: FREE (only electricity)
- **OpenAI API**: $50-100+ for 150 quests
- **Claude API**: $40-80+ for 150 quests

## 🎮 CYBERPUNK LORE COVERAGE

### Quest Categories Generated:
✅ **Main Story Quests** (All acts and endings)
✅ **Romance Quests** (Judy, Panam, River, Kerry)
✅ **Major Side Quests** (Character storylines)
✅ **Faction Quests** (Mox, Aldecaldos, etc.)
✅ **Phantom Liberty DLC** (Sample quests)
✅ **Gigs** (District-specific jobs)
✅ **Cyberpsycho Sightings** (All encounters)

### Data Sources Used:
- 🌐 **Cyberpunk Wiki**: Quest details and characters
- 🎮 **Game Files**: Dialogue and story sequences  
- 📝 **Existing Cards**: Template structure and style
- 🧠 **LLM Knowledge**: General Cyberpunk 2077 lore

## 🔍 QUALITY ASSURANCE

### Automated Checks:
✅ **YAML Validation**: Proper structure
✅ **Slovak Translation**: Content in Slovak
✅ **Cross-references**: Related content links
✅ **Elena Notes**: Chatbot guidance
✅ **Spoiler Levels**: Appropriate warnings

### Manual Review Recommended:
- Character name consistency
- Plot accuracy verification  
- Translation quality check
- Missing quest detection

## 🚀 USAGE AFTER GENERATION

### Elena Chatbot Will Support:
✅ **All quest walkthroughs**
✅ **Character relationship advice**
✅ **Romance path guidance**  
✅ **Ending requirements**
✅ **Choice consequences**
✅ **Character builds for quests**

### Total Coverage:
From **44 quests** to **~180 quests** = **300%+ improvement**

## 🎉 SUCCESS METRICS

### Before:
- Limited quest coverage
- Missing romance paths
- No DLC content
- Manual creation bottleneck

### After:
- Complete quest database
- All romance paths covered
- DLC content included
- Automated generation pipeline

**Perfect for comprehensive Cyberpunk 2077 gameplay support!** 🌟
