# 🤖 CYBERPUNK QUEST GENERATOR - LOKÁLNE LLM
# Automatic generation všetkých quest kariet using local LLM

## OVERVIEW
Script pre bulk generation všetkých Cyberpunk 2077 quest kariet using:
- **Local LLM** (Llama 3.1 70B alebo Qwen2.5 72B)
- **Cyberpunk lore database** 
- **Template system**
- **Batch processing**

## LLM OPTIONS

### 🔥 RECOMMENDED MODELS:
1. **Llama 3.1 70B Instruct** (ollama/llama3.1:70b)
   - Excellent reasoning
   - Good Slovak support
   - 40GB+ VRAM required

2. **Qwen2.5 72B Instruct** (ollama/qwen2.5:72b) 
   - Superior multilingual
   - Better Slovak translation
   - 45GB+ VRAM required

3. **Llama 3.1 8B Instruct** (ollama/llama3.1:8b)
   - Lighter option (8GB VRAM)
   - Good enough quality
   - Faster generation

### 🚀 OPTIMIZED SETUP:
- **Ollama** pre local hosting
- **GPU offloading** s CUDA
- **Batch processing** s rate limiting
- **Template-based generation**

## CYBERPUNK LORE SOURCES

### 📚 DATA COLLECTION:
1. **Cyberpunk Wiki Scraping**:
   ```
   - https://cyberpunk.fandom.com/wiki/Category:Cyberpunk_2077_Quests
   - https://cyberpunk.fandom.com/wiki/Category:Characters_(Cyberpunk_2077)
   - https://cyberpunk.fandom.com/wiki/Category:Locations_(Cyberpunk_2077)
   ```

2. **Game Data Extraction**:
   ```
   - Quest dialogue files
   - Character descriptions  
   - Location data
   - Story sequences
   ```

3. **Existing Templates**:
   ```
   - Naše 44 existing quest cards
   - YAML structure templates
   - Slovak translation patterns
   ```

## SCRIPT ARCHITECTURE

### 🏗️ COMPONENTS:
```
quest_generator/
├── data_sources/
│   ├── wiki_scraper.py      # Wiki data collection
│   ├── game_extractor.py    # Game files parsing
│   └── existing_parser.py   # Template analysis
├── llm_engine/
│   ├── ollama_client.py     # Local LLM interface
│   ├── prompt_templates.py  # Generation prompts
│   └── batch_processor.py   # Mass generation
├── generators/
│   ├── main_story.py        # Main quest generator
│   ├── side_quests.py       # Side quest generator
│   ├── romance.py           # Romance quest generator
│   └── gigs.py              # Gigs generator
└── output/
    ├── validation.py        # Quality checks
    ├── formatter.py         # YAML formatting
    └── deployer.py          # File deployment
```

## IMPLEMENTATION PLAN

### 🎯 PHASE 1: Setup (30 min)
- Install Ollama
- Download Llama 3.1 70B/8B
- Setup Python environment
- Create data collection scripts

### 🎯 PHASE 2: Data Collection (1 hour)
- Scrape Cyberpunk Wiki
- Extract existing card patterns
- Build comprehensive quest list
- Create lore knowledge base

### 🎯 PHASE 3: Generation (2 hours)
- Generate all main story quests (20 missing)
- Generate all side quests (80+ missing)
- Generate all romance quests (10+ missing)  
- Generate all gigs (50+ missing)

### 🎯 PHASE 4: Validation (30 min)
- Quality checks
- Slovak translation validation
- YAML structure verification
- Deploy to lore directory

## EXPECTED OUTPUT
- **150+ quest cards** in 3 hours
- **Consistent quality** using templates
- **Proper Slovak** with English technical terms
- **Complete coverage** of all game content

## HARDWARE REQUIREMENTS
- **GPU**: RTX 4090 (24GB) alebo RTX 3090 (24GB) pre 8B model
- **GPU**: H100 (80GB) alebo multiple GPUs pre 70B model
- **RAM**: 32GB+ system RAM
- **Storage**: 100GB+ pre model files

## COST COMPARISON
- **Local LLM**: FREE (len električka)
- **OpenAI API**: $50-100+ pre 150 questov
- **Time**: 3 hours vs 20+ hours manual

## BENEFITS
✅ **Úplná quest coverage**
✅ **Konzistentná kvalita**  
✅ **No API costs**
✅ **Offline working**
✅ **Customizable prompts**
✅ **Batch processing**
