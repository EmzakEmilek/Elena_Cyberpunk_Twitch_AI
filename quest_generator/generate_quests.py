#!/usr/bin/env python3
"""
🤖 CYBERPUNK QUEST GENERATOR - MAIN SCRIPT
Generates all missing Cyberpunk 2077 quest cards using local LLM
"""

import asyncio
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import requests
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QuestInfo:
    """Quest information structure"""
    name: str
    category: str
    act: str = None
    description: str = None
    characters: List[str] = None
    location: str = None
    prerequisites: List[str] = None
    
class OllamaClient:
    """Local LLM client using Ollama"""
    
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
    
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response using local LLM"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return ""

class QuestGenerator:
    """Main quest generator class"""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client
        self.existing_quests = self._load_existing_quests()
        self.templates = self._load_templates()
        
    def _load_existing_quests(self) -> Dict[str, Any]:
        """Load existing quest cards as examples"""
        quests = {}
        quest_dirs = [
            Path("lore/quests/main_story"),
            Path("lore/quests/side_quests"), 
            Path("lore/quests/romance_quests")
        ]
        
        for quest_dir in quest_dirs:
            if quest_dir.exists():
                for quest_file in quest_dir.glob("*.yaml"):
                    try:
                        with open(quest_file, 'r', encoding='utf-8') as f:
                            quest_data = yaml.safe_load(f)
                            quests[quest_file.stem] = quest_data
                    except Exception as e:
                        logger.warning(f"Failed to load {quest_file}: {e}")
        
        logger.info(f"Loaded {len(quests)} existing quest templates")
        return quests
    
    def _load_templates(self) -> Dict[str, str]:
        """Load quest generation templates"""
        return {
            "system_prompt": """
You are an expert Cyberpunk 2077 quest designer and Slovak translator. 
Create detailed quest cards in YAML format following the exact structure of existing examples.
Requirements:
- Content in Slovak language with English technical terms
- Maintain consistent YAML structure
- Include elena_notes section for chatbot guidance
- Set appropriate spoiler levels
- Add cross-references to related content
- Focus on gameplay utility and character development
""",
            
            "main_story_template": """
Create a main story quest card for: {quest_name}

Context: {context}
Characters: {characters}
Location: {location}

Use this YAML structure exactly:
```yaml
type: "quest"
title: "{quest_name}"
category: "main_story"

summary: "Brief Slovak description with key points"

key_points:
  - "Key gameplay element 1"
  - "Character development aspect"
  - "Story progression point"

story_context:
  act: "Act X"
  position: "Quest position in storyline"
  importance: "Why this quest matters"

characters:
  - "V (protagonist)"
  - "Other key characters"

objectives:
  - "Main quest objective"
  - "Secondary objectives"

choices:
  main_decision:
    description: "Key choice description"
    options:
      - "Option 1 - consequences"
      - "Option 2 - consequences"
    consequences: "Impact on story/relationships"

themes:
  - "Central theme 1"
  - "Character development theme"

related:
  - "related_quest_1"
  - "related_character_1"

elena_notes:
  talking_points:
    - "Key discussion points"
    - "Important gameplay aspects"
  spoiler_level: "low/medium/high/maximum"
  conversation_context:
    - "Context for chatbot responses"

technical_metadata:
  last_updated: "2025-08-24"
  translation_status: "completed"
  language: "slovak"
```

Generate ONLY the YAML content, no additional text.
""",

            "side_quest_template": """
Create a side quest card for: {quest_name}

Context: {context}
Type: {quest_type}
Characters: {characters}

Follow the same YAML structure as main story quests but with:
- category: "side_quest"
- Appropriate quest type context
- Character-specific themes
- Side quest specific objectives

Generate ONLY the YAML content.
""",

            "romance_template": """
Create a romance quest card for: {quest_name}

Romance Character: {romance_character}
Requirements: {requirements}
Context: {context}

Follow the YAML structure with:
- category: "romance"
- Romance-specific themes
- Relationship development
- Emotional moments
- Prerequisites and requirements

Generate ONLY the YAML content.
"""
        }
    
    async def generate_quest_card(self, quest_info: QuestInfo) -> str:
        """Generate a single quest card"""
        logger.info(f"Generating quest: {quest_info.name}")
        
        # Select appropriate template
        if quest_info.category == "main_story":
            template_key = "main_story_template"
        elif quest_info.category == "romance":
            template_key = "romance_template"
        else:
            template_key = "side_quest_template"
        
        # Format prompt
        prompt = self.templates[template_key].format(
            quest_name=quest_info.name,
            context=quest_info.description or "Unknown context",
            characters=", ".join(quest_info.characters or ["Unknown"]),
            location=quest_info.location or "Unknown location",
            quest_type=quest_info.category,
            romance_character=quest_info.characters[0] if quest_info.characters else "Unknown",
            requirements=quest_info.prerequisites or "Unknown requirements"
        )
        
        # Generate with LLM
        result = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.templates["system_prompt"]
        )
        
        return result
    
    async def generate_all_missing_quests(self):
        """Generate all missing quest cards"""
        # Define missing quests
        missing_quests = [
            # Main Story - Missing quests
            QuestInfo("Where Is My Mind", "main_story", "Act 3", "Final mission leading to multiple endings"),
            QuestInfo("Path of Glory", "main_story", "Act 3", "Corpo ending path"),
            QuestInfo("All Along the Watchtower", "main_story", "Act 3", "Rogue ending path"),
            QuestInfo("New Dawn Fades", "main_story", "Act 3", "Solo ending sequence"),
            QuestInfo("The Sun", "main_story", "Act 3", "Legend ending"),
            QuestInfo("The Star", "main_story", "Act 3", "Nomad ending"),
            QuestInfo("Temperance", "main_story", "Act 3", "Johnny ending"),
            QuestInfo("The Devil", "main_story", "Act 3", "Arasaka ending"),
            
            # Major Side Quests
            QuestInfo("Pisces", "side_quest", None, "Judy storyline continuation"),
            QuestInfo("I Fought the Law", "side_quest", None, "River Ward introduction"),
            QuestInfo("The Hunt", "side_quest", None, "River Ward main quest"),
            QuestInfo("Epistrophy", "side_quest", None, "Delamain AI quest chain"),
            QuestInfo("Dream On", "side_quest", None, "Corpo conspiracy quest"),
            QuestInfo("I Walk the Line", "side_quest", None, "Netwatch vs Voodooboys"),
            QuestInfo("Violence", "side_quest", None, "6th Street gang quest"),
            QuestInfo("Heroes", "side_quest", None, "Mox faction quest"),
            QuestInfo("Space Oddity", "side_quest", None, "Reference quest"),
            QuestInfo("Machine Gun", "side_quest", None, "Johnny Silverhand reference"),
            
            # Romance-specific
            QuestInfo("With a Little Help from My Friends", "romance", None, "Panam support quest"),
            QuestInfo("Off the Leash", "romance", None, "Kerry Eurodyne romance continuation"),
            
            # Phantom Liberty (sample)
            QuestInfo("Dog Eat Dog", "side_quest", "Phantom Liberty", "DLC opening quest"),
            QuestInfo("Hole in the Sky", "side_quest", "Phantom Liberty", "Songbird introduction"),
            QuestInfo("The Lamp", "side_quest", "Phantom Liberty", "Myers storyline"),
        ]
        
        logger.info(f"Starting generation of {len(missing_quests)} quest cards...")
        
        for i, quest_info in enumerate(missing_quests):
            try:
                # Generate quest card
                yaml_content = await self.generate_quest_card(quest_info)
                
                if yaml_content.strip():
                    # Save to appropriate directory
                    if quest_info.category == "main_story":
                        output_dir = Path("lore/quests/main_story")
                    elif quest_info.category == "romance":
                        output_dir = Path("lore/quests/romance_quests")
                    else:
                        output_dir = Path("lore/quests/side_quests")
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Clean filename
                    filename = quest_info.name.lower().replace(" ", "_").replace("'", "").replace("?", "")
                    output_file = output_dir / f"{filename}.yaml"
                    
                    # Save file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        # Clean YAML content
                        cleaned_content = yaml_content.strip()
                        if cleaned_content.startswith("```yaml"):
                            cleaned_content = cleaned_content.replace("```yaml", "").replace("```", "").strip()
                        f.write(cleaned_content)
                    
                    logger.info(f"✅ Generated: {filename}.yaml ({i+1}/{len(missing_quests)})")
                else:
                    logger.error(f"❌ Failed to generate: {quest_info.name}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error generating {quest_info.name}: {e}")
        
        logger.info("🎉 Quest generation completed!")

async def main():
    """Main execution function"""
    logger.info("🤖 Starting Cyberpunk Quest Generator...")
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        logger.info(f"Available models: {[m['name'] for m in models]}")
    except Exception as e:
        logger.error(f"❌ Ollama not accessible: {e}")
        logger.info("Please start Ollama: 'ollama serve'")
        return
    
    # Initialize generator
    llm = OllamaClient(model="llama3.1:8b")  # Change to your preferred model
    generator = QuestGenerator(llm)
    
    # Generate all missing quests
    await generator.generate_all_missing_quests()
    
    # Report results
    quest_dirs = [
        Path("lore/quests/main_story"),
        Path("lore/quests/side_quests"),
        Path("lore/quests/romance_quests")
    ]
    
    total_quests = 0
    for quest_dir in quest_dirs:
        if quest_dir.exists():
            count = len(list(quest_dir.glob("*.yaml")))
            total_quests += count
            logger.info(f"{quest_dir.name}: {count} quests")
    
    logger.info(f"🎯 Total quest cards: {total_quests}")

if __name__ == "__main__":
    asyncio.run(main())
