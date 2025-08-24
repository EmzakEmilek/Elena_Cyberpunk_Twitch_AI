#!/usr/bin/env python3
"""
🌍 SLOVAKIA TRANSLATOR
Preloží všetky YAML karty do slovenčiny pomocou Llama 3.1:8b
"""

import yaml
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import re
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TranslationStats:
    """Štatistiky prekladu"""
    total_cards: int = 0
    translated_cards: int = 0
    skipped_cards: int = 0
    failed_cards: int = 0
    start_time: float = 0
    
    def get_progress(self) -> str:
        if self.total_cards == 0:
            return "0%"
        return f"{(self.translated_cards / self.total_cards * 100):.1f}%"
    
    def get_eta(self) -> str:
        if self.translated_cards == 0:
            return "Neznámy"
        
        elapsed = time.time() - self.start_time
        avg_time = elapsed / self.translated_cards
        remaining = (self.total_cards - self.translated_cards) * avg_time
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"{hours}h {minutes}m"

class OllamaTranslator:
    """Prekladateľ pomocou Ollama Llama 3.1"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        self.session = requests.Session()
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test Ollama connection"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model_name not in model_names:
                    logger.warning(f"⚠️ Model {self.model_name} nie je nájdený!")
                    logger.info(f"📋 Dostupné modely: {', '.join(model_names)}")
                else:
                    logger.info(f"✅ Ollama pripojené - model {self.model_name}")
            else:
                raise Exception(f"Ollama neodpovedá: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Chyba pripojenia k Ollama: {e}")
            logger.info("💡 Spusti: ollama serve")
            raise
    
    def translate_text(self, text: str, context: str = "") -> str:
        """Preloží text do slovenčiny"""
        if not text or not text.strip():
            return text
        
        # Skip if already in Slovak (contains Slovak characters)
        if self._is_likely_slovak(text):
            logger.debug(f"⏭️ Preskakujem (už SK): {text[:50]}...")
            return text
        
        # Skip technical terms, names, IDs
        if self._is_technical_term(text):
            logger.debug(f"⏭️ Preskakujem (technický): {text}")
            return text
        
        prompt = self._build_translation_prompt(text, context)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                translated = result['response'].strip()
                
                # Clean up the response
                translated = self._clean_translation(translated)
                
                logger.debug(f"🔄 '{text[:30]}...' → '{translated[:30]}...'")
                return translated
            else:
                logger.error(f"❌ Translation API error: {response.status_code}")
                return text
                
        except Exception as e:
            logger.error(f"❌ Translation failed for '{text[:30]}...': {e}")
            return text
    
    def _is_likely_slovak(self, text: str) -> bool:
        """Check if text is likely already in Slovak"""
        slovak_chars = set('áäčďéíĺľňóôŕšťúýž')
        slovak_words = {
            'je', 'sa', 'na', 'do', 'zo', 'pre', 'ako', 'kde', 'čo', 'kto', 
            'má', 'môže', 'nie', 'aby', 'alebo', 'však', 'len', 'už', 'až',
            'ochranárska', 'temperamentná', 'lojálna', 'nezávislá',
            'vodcovstvo', 'bojové', 'technické', 'znalosti', 'schopnosti'
        }
        
        # Check for Slovak characters (must have at least 2)
        slovak_char_count = sum(1 for char in text.lower() if char in slovak_chars)
        if slovak_char_count >= 2:
            return True
        
        # Check for Slovak words (must be majority)
        words = text.lower().split()
        if len(words) == 0:
            return False
            
        slovak_word_count = sum(1 for word in words if word in slovak_words)
        
        # Only consider Slovak if more than 70% of words are Slovak
        return slovak_word_count > len(words) * 0.7
    
    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term that shouldn't be translated"""
        
        # Skip very short texts
        if len(text) < 2:
            return True
            
        # Technical patterns - narrowed down
        technical_patterns = [
            r'^[a-z_]+_[a-z_]+$',  # snake_case with underscore
            r'^[A-Z_]{3,}$',       # UPPER_CASE 3+ chars
            r'^\d+',               # starts with number
            r'^[a-f0-9-]{8,}$',    # IDs/hashes
            r'^char_|^loc_|^quest_|^faction_'  # our ID prefixes
        ]
        
        # Don't translate obvious technical IDs
        if any(re.match(pattern, text) for pattern in technical_patterns):
            return True
            
        # Don't translate character names, location names
        if text in ['V', 'Johnny Silverhand', 'Night City', 'Arasaka', 'Militech']:
            return True
        
        return False
    
    def _build_translation_prompt(self, text: str, context: str) -> str:
        """Build translation prompt for LLM"""
        return f"""Prelož do slovenčiny (nie srbčiny): "{text}"

Odpoveď iba preložený text."""
    
    def _clean_translation(self, translated: str) -> str:
        """Clean up translated text"""
        # Remove common LLM artifacts
        cleaned = translated.strip()
        
        # Remove quotation marks if they wrap the entire text
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        
        # Remove "SLOVENSKÝ PREKLAD:" prefix if present
        prefixes = [
            "SLOVENSKÝ PREKLAD:", "Preklad:", "Slovensky:",
            "SLOVENSKÝ PREKLAD (správna slovenčina):",
            "TEXT NA PREKLAD:", "PREKLAD:", "KONTEXT:",
            "PRAVIDLÁ:", "PRÍKLADY"
        ]
        for prefix in prefixes:
            if prefix in cleaned:
                # Find the position after the prefix
                pos = cleaned.find(prefix)
                if pos != -1:
                    # Look for the actual translation after the prefix
                    after_prefix = cleaned[pos + len(prefix):].strip()
                    if after_prefix:
                        cleaned = after_prefix
                        break
        
        # Remove everything before a colon if it looks like a prompt
        if ":" in cleaned and len(cleaned.split(":")[0]) > 20:
            parts = cleaned.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                cleaned = parts[1].strip()
        
        # If the translation still contains prompt text, try to extract just the translation
        lines = cleaned.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not any(keyword in line.upper() for keyword in [
                'PRAVIDLÁ', 'PRÍKLADY', 'KONTEXT', 'TEXT NA PREKLAD', 
                'SLOVENSKÝ PREKLAD', 'NIE SRBSKY', 'HELLO WORLD'
            ]):
                # This looks like actual translated content
                return line
        
        # If all else fails, return just the first meaningful line
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:  # Short enough to be a translation
                return line
        
        return cleaned

class CardTranslator:
    """Hlavný prekladateľ YAML kariet"""
    
    def __init__(self, translator: OllamaTranslator):
        self.translator = translator
        self.stats = TranslationStats()
        
        # Fields to translate
        self.translatable_fields = {
            'description', 'summary', 'content', 'note', 'elena_notes',
            'background', 'history', 'details', 'usage', 'effects',
            'characteristics', 'culture', 'economy', 'entertainment'
        }
        
        # Fields to skip (technical/identifiers)
        self.skip_fields = {
            'id', 'name', 'filename', 'category', 'subcategory',
            'related_quests', 'related_characters', 'related_locations',
            'tags', 'cross_references', 'dependencies'
        }
    
    def translate_all_cards(self, lore_path: str = "lore"):
        """Preloží všetky karty v lore priečinku"""
        logger.info("🚀 Spúšťam hromadný preklad kariet...")
        
        lore_dir = Path(lore_path)
        yaml_files = list(lore_dir.rglob("*.yaml"))
        
        self.stats.total_cards = len(yaml_files)
        self.stats.start_time = time.time()
        
        logger.info(f"📊 Nájdených {self.stats.total_cards} YAML kariet")
        
        for i, yaml_file in enumerate(yaml_files, 1):
            try:
                logger.info(f"🔄 [{i}/{self.stats.total_cards}] {yaml_file.name}")
                
                if self.translate_card(yaml_file):
                    self.stats.translated_cards += 1
                else:
                    self.stats.skipped_cards += 1
                
                # Progress report every 10 cards
                if i % 10 == 0:
                    self._print_progress()
                
                # Small delay to prevent overload
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Chyba pri spracovaní {yaml_file}: {e}")
                self.stats.failed_cards += 1
        
        self._print_final_stats()
    
    def translate_card(self, yaml_file: Path) -> bool:
        """Preloží jednu kartu"""
        try:
            # Load YAML
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"⚠️ Prázdny súbor: {yaml_file}")
                return False
            
            # Track if anything was translated
            translated_something = False
            
            # Translate recursively
            if self._translate_dict(data, str(yaml_file.stem)):
                translated_something = True
            
            # Save if translated
            if translated_something:
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, 
                             allow_unicode=True, sort_keys=False, indent=2)
                
                logger.info(f"✅ Preložené: {yaml_file.name}")
                return True
            else:
                logger.debug(f"⏭️ Bez zmien: {yaml_file.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Chyba pri preklade {yaml_file}: {e}")
            return False
    
    def _translate_dict(self, data: Dict[str, Any], context: str) -> bool:
        """Preloží slovník rekurzívne"""
        translated_something = False
        
        for key, value in data.items():
            if isinstance(value, str):
                # Translate string values
                if key.lower() in self.translatable_fields:
                    if len(value.strip()) > 0:
                        translated = self.translator.translate_text(value, context)
                        if translated != value:
                            data[key] = translated
                            translated_something = True
                            
            elif isinstance(value, list):
                # Translate list items
                if key.lower() in self.translatable_fields:
                    for i, item in enumerate(value):
                        if isinstance(item, str) and len(item.strip()) > 0:
                            translated = self.translator.translate_text(item, context)
                            if translated != item:
                                value[i] = translated
                                translated_something = True
                                
            elif isinstance(value, dict):
                # Recurse into nested dicts
                if self._translate_dict(value, context):
                    translated_something = True
        
        return translated_something
    
    def _print_progress(self):
        """Vypíše aktuálny progres"""
        logger.info(f"📈 Progres: {self.stats.get_progress()} | "
                   f"Preložené: {self.stats.translated_cards} | "
                   f"Preskočené: {self.stats.skipped_cards} | "
                   f"ETA: {self.stats.get_eta()}")
    
    def _print_final_stats(self):
        """Vypíše finálne štatistiky"""
        elapsed = time.time() - self.stats.start_time
        
        logger.info("🎉 PREKLAD DOKONČENÝ!")
        logger.info(f"📊 ŠTATISTIKY:")
        logger.info(f"   • Celkom kariet: {self.stats.total_cards}")
        logger.info(f"   • Preložených: {self.stats.translated_cards}")
        logger.info(f"   • Preskočených: {self.stats.skipped_cards}")
        logger.info(f"   • Chybných: {self.stats.failed_cards}")
        logger.info(f"   • Celkový čas: {elapsed/60:.1f} minút")
        logger.info(f"   • Priemerný čas/kartu: {elapsed/self.stats.total_cards:.1f}s")

def main():
    """Hlavná funkcia"""
    print("🌍 SLOVAKIA CARD TRANSLATOR")
    print("=" * 50)
    
    try:
        # Initialize translator
        translator = OllamaTranslator("llama3.1:8b")
        card_translator = CardTranslator(translator)
        
        # Start translation
        card_translator.translate_all_cards()
        
    except KeyboardInterrupt:
        print("\n⏹️ Preklad prerušený používateľom")
    except Exception as e:
        print(f"\n❌ Kritická chyba: {e}")

if __name__ == "__main__":
    main()
