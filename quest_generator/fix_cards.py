#!/usr/bin/env python3
"""
🌍🔧 COMPLETE CARD PROCESSOR
1. PRELOŽÍ všetky karty do slovenčiny (Llama 3.1)
2. OPRAVÍ všetky problémy v RAG kartách:
   - Duplicitné kľúče
   - Mojibake (zlé kódovanie)  
   - Mix jazykov
   - Nejednotné schémy
   - Spoilery
"""

import yaml
import json
import re
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Set
from dataclasses import dataclass
import logging
from pydantic import BaseModel, Field, ValidationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Štatistiky spracovania"""
    files_processed: int = 0
    files_modified: int = 0
    files_failed: int = 0
    texts_translated: int = 0
    mojibake_fixed: int = 0
    duplicate_keys_fixed: int = 0
    spoilers_extracted: int = 0
    start_time: float = 0
    
    def get_progress(self) -> str:
        if self.total_cards == 0:
            return "0%"
        processed = self.translated_cards + self.fixed_cards
        return f"{(processed / self.total_cards * 100):.1f}%"

@dataclass
class ValidationIssue:
    """Problém v karte"""
    file_path: str
    issue_type: str
    description: str
    severity: str  # "error", "warning", "info"
    fix_suggestion: str = ""


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
                logger.info(f"✅ Ollama pripojené - model {self.model_name}")
            else:
                raise Exception(f"Ollama neodpovedá: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Chyba pripojenia k Ollama: {e}")
            raise
    
    def translate_text(self, text: str, context: str = "") -> str:
        """Preloží text do slovenčiny"""
        if not text or not text.strip():
            return text
        
        # Skip if already in Slovak
        if self._is_likely_slovak(text):
            return text
        
        # Skip technical terms
        if self._is_technical_term(text):
            return text
        
        # SIMPLIFIED PROMPT - no rules visible in output
        prompt = f'Translate to Slovak language: "{text}"\n\nAnswer only the Slovak translation, nothing else.'
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "max_tokens": 100
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                translated = result['response'].strip()
                
                # Clean up the response
                translated = self._clean_translation(translated)
                
                # Validate it's actually Slovak
                if self._is_slovenian_not_slovak(translated):
                    logger.warning(f"⚠️ Possible Slovenian detected: {translated[:30]}...")
                    return self._fix_slovenian_to_slovak(translated)
                
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
        return slovak_word_count > len(words) * 0.7
    
    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term that shouldn't be translated"""
        if len(text) < 2:
            return True
            
        # Technical patterns
        technical_patterns = [
            r'^[a-z_]+_[a-z_]+$',  # snake_case
            r'^[A-Z_]{3,}$',       # UPPER_CASE
            r'^\d+',               # starts with number
            r'^char_|^loc_|^quest_|^faction_'  # our ID prefixes
        ]
        
        if any(re.match(pattern, text) for pattern in technical_patterns):
            return True
            
        # Don't translate names, IDs
        if text in ['V', 'Johnny Silverhand', 'Night City', 'Arasaka', 'Militech']:
            return True
        
        return False
    
    def _clean_translation(self, translated: str) -> str:
        """Clean up translated text"""
        cleaned = translated.strip()
        
        # Remove quotation marks
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        
        # Remove prompt artifacts
        prefixes = [
            "SLOVENSKÝ PREKLAD:", "Preklad:", "Slovensky:",
            "TEXT NA PREKLAD:", "PREKLAD:", "KONTEXT:",
            "PRAVIDLÁ:", "PRÍKLADY"
        ]
        
        for prefix in prefixes:
            if prefix in cleaned:
                pos = cleaned.find(prefix)
                if pos != -1:
                    after_prefix = cleaned[pos + len(prefix):].strip()
                    if after_prefix:
                        cleaned = after_prefix
                        break
        
        # Remove everything before colon if it looks like a prompt
        if ":" in cleaned and len(cleaned.split(":")[0]) > 20:
            parts = cleaned.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                cleaned = parts[1].strip()
        
        # Extract just the translation from multiple lines
        lines = cleaned.split('\n')
        for line in lines:
            line = line.strip()
            if line and not any(keyword in line.upper() for keyword in [
                'PRAVIDLÁ', 'PRÍKLADY', 'KONTEXT', 'TEXT NA PREKLAD', 
                'SLOVENSKÝ PREKLAD', 'NIE SRBSKY', 'HELLO WORLD'
            ]):
                return line
        
        return cleaned
    
    def _is_slovenian_not_slovak(self, text: str) -> bool:
        """Detect if text is Slovenian instead of Slovak"""
        slovenian_words = {
            'naslov', 'ime', 'spola', 'frakcija', 'približenje', 'sisteme',
            'priroda', 'sila', 'príroda', 'možnosti', 'obsah', 'zámer',
            'lahko', 'mora', 'lahko', 'priložnost', 'možnost'
        }
        
        words = text.lower().split()
        slovenian_count = sum(1 for word in words if word in slovenian_words)
        
        return slovenian_count > 0 and len(words) > 0
    
    def _fix_slovenian_to_slovak(self, text: str) -> str:
        """Fix common Slovenian -> Slovak translations"""
        fixes = {
            'naslov': 'názov',
            'ime': 'meno', 
            'spola': 'pohlavie',
            'frakcija': 'frakcia',
            'približenje': 'prístup',
            'sisteme': 'systémy',
            'príroda': 'povaha',
            'obydlie': 'bydlisko',
            'archetype': 'archetyp',
            'motivácia': 'motivácia',
            'posobnosti': 'schopnosti',
            'slabosti': 'slabosti',
            'obdobi': 'obdobie',
            'možnosti': 'možnosti',
            'vplivy': 'vplyvy',
            'priamo': 'priamo',
            'približenie': 'prístup',
            'fokus': 'zameranie',
            'výkon': 'výkon',
            'oblast': 'oblasť',
            'sposobnosti': 'schopnosti'
        }
        
        fixed = text
        for slo, svk in fixes.items():
            fixed = re.sub(r'\b' + slo + r'\b', svk, fixed, flags=re.IGNORECASE)
        
        return fixed

class CardSchema(BaseModel):
    """Pydantic schéma pre karty"""
    type: str = Field(..., pattern=r"^(character|location|quest|faction|technology|weapon|cyberware)$")
    id: str = Field(..., pattern=r"^[a-z_]+$")
    title: str = Field(..., min_length=1)
    aliases: List[str] = Field(default_factory=list)
    category: str = Field(...)
    lang: str = Field(default="sk", pattern=r"^(sk|en)$")
    
    content: Dict[str, Any] = Field(...)
    quotes: List[Dict[str, str]] = Field(default_factory=list)
    spoilers: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(...)
    related: List[Dict[str, str]] = Field(default_factory=list)

class YAMLCardFixer:
    """Kombinovaný translator + fixer YAML kariet"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.stats = ProcessingStats()
        
        # Initialize translator
        self.translator = OllamaTranslator()
        
        # Mojibake mapping
        self.mojibake_fixes = {
            'ÄŤ': 'č', 'Äť': 'Č',
            'Ă˝': 'ý', 'ĂŤ': 'í', 'Ăˇ': 'á', 'Ă´': 'ô',
            'ĹĄ': 'š', 'Ĺ˝': 'ž', 'ĂŤ': 'é', 'ĹĽ': 'ť',
            'PouliÄŤnĂ©': 'Pouličné',
            'NomĂˇd': 'Nomád',
            'KorporĂˇtny': 'Korporátny',
            'PrĂ­beh': 'Príbeh',
            'preloĹľenĂ©': 'preložené',
            'termĂ­nmi': 'termínmi',
            'ĹľenĂ©': 'žené',
            'konverz': 'konverzácia'
        }
        
        # Spoiler keywords
        self.spoiler_keywords = {
            'smrť', 'umiera', 'zomrie', 'fatálne', 'tragédia', 'zabitý',
            'death', 'dies', 'killed', 'fatal', 'tragedy', 'murder'
        }
    
    def process_all_cards(self, lore_dir: Path):
        """Process all cards: translate + fix"""
        logger.info("🚀 Starting combined translation and fixing process...")
        
        yaml_files = list(lore_dir.rglob("*.yaml")) + list(lore_dir.rglob("*.yml"))
        total_files = len(yaml_files)
        
        logger.info(f"📁 Found {total_files} YAML files to process")
        
        for i, file_path in enumerate(yaml_files, 1):
            logger.info(f"🔄 Processing [{i}/{total_files}] {file_path.name}")
            
            try:
                self.process_single_card(file_path)
                self.stats.files_processed += 1
                
                # Progress every 10 files
                if i % 10 == 0:
                    logger.info(f"📊 Progress: {i}/{total_files} files processed")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                self.stats.files_failed += 1
        
        self.print_summary()
    
    def process_single_card(self, file_path: Path):
        """Process single card: translate + fix"""
        # 1. Load original
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ Failed to parse YAML {file_path}: {e}")
            self.stats.files_failed += 1
            return
        
        if not data:
            return
        
        original_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        # 2. Translate content
        translated_data = self.translate_card_content(data)
        
        # 3. Fix mojibake and structure
        fixed_data = self.fix_card_structure(translated_data)
        
        # 4. Check if changes were made
        final_data_str = json.dumps(fixed_data, sort_keys=True, ensure_ascii=False)
        
        if final_data_str != original_data:
            self.save_card(file_path, fixed_data)
            self.stats.files_modified += 1
            logger.info(f"✅ {file_path.name}: Translated and fixed")
        else:
            logger.info(f"✅ {file_path.name}: No changes needed")
    
    def translate_card_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate card content to Slovak"""
        if not isinstance(data, dict):
            return data
        
        translated = {}
        
        for key, value in data.items():
            # Don't translate technical keys
            if key in ['id', 'type', 'category', 'tags', 'difficulty', 'status']:
                translated[key] = value
                continue
            
            # Translate key if needed
            translated_key = key
            if isinstance(key, str) and not self.translator._is_technical_term(key):
                new_key = self.translator.translate_text(key)
                if new_key != key:
                    translated_key = new_key
                    self.stats.texts_translated += 1
            
            # Translate value based on type
            if isinstance(value, str):
                translated_value = self.translator.translate_text(value)
                if translated_value != value:
                    self.stats.texts_translated += 1
            elif isinstance(value, dict):
                translated_value = self.translate_card_content(value)
            elif isinstance(value, list):
                translated_value = []
                for item in value:
                    if isinstance(item, str):
                        new_item = self.translator.translate_text(item)
                        translated_value.append(new_item)
                        if new_item != item:
                            self.stats.texts_translated += 1
                    elif isinstance(item, dict):
                        translated_value.append(self.translate_card_content(item))
                    else:
                        translated_value.append(item)
            else:
                translated_value = value
            
            translated[translated_key] = translated_value
        
        return translated
    
    def fix_card_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix card structure: mojibake + standardize"""
        # 1. Fix mojibake in all strings
        fixed_data = self.fix_mojibake_recursive(data)
        
        # 2. Standardize schema
        standardized = self.standardize_schema(fixed_data)
        
        return standardized
    
    def fix_mojibake_recursive(self, obj):
        """Recursively fix mojibake in data structure"""
        if isinstance(obj, str):
            fixed = self.fix_mojibake(obj)
            if fixed != obj:
                self.stats.mojibake_fixed += 1
            return fixed
        elif isinstance(obj, dict):
            return {k: self.fix_mojibake_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.fix_mojibake_recursive(item) for item in obj]
        else:
            return obj
    
    def save_card(self, file_path: Path, data: Dict[str, Any]):
        """Save processed card"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.error(f"❌ Failed to save {file_path}: {e}")
            self.stats.files_failed += 1
    
    def print_summary(self):
        """Print processing summary"""
        logger.info("=" * 60)
        logger.info("📊 PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Files processed: {self.stats.files_processed}")
        logger.info(f"✏️ Files modified: {self.stats.files_modified}")
        logger.info(f"❌ Files failed: {self.stats.files_failed}")
        logger.info(f"🌍 Texts translated: {self.stats.texts_translated}")
        logger.info(f"🔧 Mojibake fixed: {self.stats.mojibake_fixed}")
        logger.info(f"🔑 Duplicate keys: {self.stats.duplicate_keys_fixed}")
        logger.info(f"⚠️ Spoilers extracted: {self.stats.spoilers_extracted}")
        logger.info("=" * 60)
    
    def detect_duplicates(self, file_path: Path) -> List[ValidationIssue]:
        """Deteguj duplicitné kľúče"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple duplicate key detection by parsing lines
            seen_keys = set()
            duplicates = []
            
            for line_num, line in enumerate(content.split('\n'), 1):
                if ':' in line and not line.strip().startswith('#'):
                    key = line.split(':')[0].strip()
                    if key and not key.startswith('-'):
                        if key in seen_keys:
                            duplicates.append((key, line_num))
                        else:
                            seen_keys.add(key)
            
            for key, line_num in duplicates:
                issues.append(ValidationIssue(
                    file_path=str(file_path),
                    issue_type="duplicate_keys",
                    description=f"Duplicitný kľúč '{key}' na riadku {line_num}",
                    severity="error",
                    fix_suggestion="Odstráň duplicitné kľúče, ponechaj len posledný"
                ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(file_path),
                issue_type="yaml_syntax",
                description=f"YAML syntax error: {e}",
                severity="error"
            ))
        return issues
    
    def fix_mojibake(self, text: str) -> str:
        """Oprav mojibake"""
        for wrong, correct in self.mojibake_fixes.items():
            text = text.replace(wrong, correct)
        return text
    
    def detect_language_mix(self, text: str) -> bool:
        """Deteguj mix jazykov"""
        english_patterns = [
            r'\b(the|and|or|of|in|to|for|with|by|from|at|on)\b',
            r'\b(character|location|quest|mission|weapon|system)\b',
            r'\b(becoming|fighting|working|leading|managing)\b'
        ]
        
        for pattern in english_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def extract_spoilers(self, content: Dict[str, Any]) -> tuple:
        """Extrahuj spoilery z contentu"""
        spoilers = {}
        
        def check_for_spoilers(obj, path=""):
            if isinstance(obj, str):
                for keyword in self.spoiler_keywords:
                    if keyword.lower() in obj.lower():
                        spoilers[path] = {
                            "content": obj,
                            "reason": f"Obsahuje spoiler keyword: {keyword}",
                            "allow_if_user_confirms": True
                        }
                        self.stats.spoilers_extracted += 1
                        return "[SPOILER REMOVED - ask user first]"
            elif isinstance(obj, dict):
                return {k: check_for_spoilers(v, f"{path}.{k}") for k, v in obj.items()}
            elif isinstance(obj, list):
                return [check_for_spoilers(item, f"{path}[{i}]") for i, item in enumerate(obj)]
            return obj
        
        cleaned_content = check_for_spoilers(content)
        return cleaned_content, spoilers
    
    def standardize_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardizuj schému karty"""
        # Detect card type
        card_type = data.get('type', 'character')
        
        # Standardize ID
        if 'character_id' in data:
            data['id'] = data.pop('character_id')
        elif 'char_id' in data:
            data['id'] = data.pop('char_id')
        
        # Ensure required fields
        standardized = {
            'type': card_type,
            'id': data.get('id', f"{card_type}_unknown"),
            'title': data.get('title', data.get('name', 'Unknown')),
            'aliases': data.get('aliases', []),
            'category': data.get('category', f"{card_type}_unknown"),
            'lang': 'sk'
        }
        
        # Extract and clean content
        content = {}
        for key, value in data.items():
            if key not in ['type', 'id', 'title', 'aliases', 'category', 'lang', 'meta', 'related']:
                content[key] = value
        
        # Clean content and extract spoilers
        cleaned_content, spoilers = self.extract_spoilers(content)
        standardized['content'] = cleaned_content
        
        if spoilers:
            standardized['spoilers'] = spoilers
        
        # Add metadata
        standardized['meta'] = {
            'last_updated': '2025-08-24',
            'translation_status': 'auto_fixed',
            'issues_fixed': [],
            'source': 'Cyberpunk 2077 Fandom Wiki'
        }
        
        # Add related if exists
        if data.get('related_cards'):
            standardized['related'] = [
                {'id': card_id} for card_id in data['related_cards']
            ]
        
        return standardized
    
    def validate_card(self, data: Dict[str, Any], file_path: str) -> List[ValidationIssue]:
        """Validuj kartu cez Pydantic"""
        issues = []
        try:
            CardSchema(**data)
        except ValidationError as e:
            for error in e.errors():
                issues.append(ValidationIssue(
                    file_path=file_path,
                    issue_type="schema_validation",
                    description=f"Validation error: {error['msg']} at {error['loc']}",
                    severity="warning"
                ))
        return issues
    
    def fix_card(self, file_path: Path) -> bool:
        """Oprav jednu kartu"""
        logger.info(f"🔧 Opravujem: {file_path.name}")
        
        try:
            # Load original
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix mojibake
            content = self.fix_mojibake(content)
            
            # Parse YAML
            data = yaml.safe_load(content)
            if not data:
                logger.warning(f"⚠️ Prázdny súbor: {file_path}")
                return False
            
            # Detect issues
            duplicate_issues = self.detect_duplicates(file_path)
            self.issues.extend(duplicate_issues)
            
            # Standardize schema
            standardized_data = self.standardize_schema(data)
            
            # Validate
            validation_issues = self.validate_card(standardized_data, str(file_path))
            self.issues.extend(validation_issues)
            
            # Save fixed version
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(standardized_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            logger.info(f"✅ Opravené: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chyba pri oprave {file_path}: {e}")
            self.issues.append(ValidationIssue(
                file_path=str(file_path),
                issue_type="fix_error",
                description=str(e),
                severity="error"
            ))
            return False
    
    def fix_all_cards(self, lore_path: str = "lore") -> Dict[str, int]:
        """Oprav všetky karty"""
        logger.info("🚀 Spúšťam opravu všetkých kariet...")
        
        lore_dir = Path(lore_path)
        yaml_files = list(lore_dir.rglob("*.yaml"))
        
        stats = {
            'total': len(yaml_files),
            'fixed': 0,
            'failed': 0,
            'issues_found': 0
        }
        
        for yaml_file in yaml_files:
            if self.fix_card(yaml_file):
                stats['fixed'] += 1
            else:
                stats['failed'] += 1
        
        stats['issues_found'] = len(self.issues)
        
        # Generate report
        self.generate_report()
        
        return stats
    
    def generate_report(self):
        """Vygeneruj report o problémoch"""
        report_path = "card_validation_report.json"
        
        report = {
            'timestamp': '2025-08-24T10:30:00',
            'summary': {
                'total_issues': len(self.issues),
                'errors': len([i for i in self.issues if i.severity == 'error']),
                'warnings': len([i for i in self.issues if i.severity == 'warning']),
                'info': len([i for i in self.issues if i.severity == 'info'])
            },
            'issues': [
                {
                    'file': issue.file_path,
                    'type': issue.issue_type,
                    'description': issue.description,
                    'severity': issue.severity,
                    'fix_suggestion': issue.fix_suggestion
                }
                for issue in self.issues
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Report uložený: {report_path}")

def main():
    """Hlavná funkcia - kombinovaný preklad + fix"""
    print("🌍🔧 COMPLETE CARD PROCESSOR")
    print("1. PRELOŽÍ všetky karty do slovenčiny (Llama 3.1)")
    print("2. OPRAVÍ všetky problémy v RAG kartách")
    print("=" * 60)
    
    # Find lore directory
    lore_dir = Path("../lore")
    if not lore_dir.exists():
        lore_dir = Path("lore")
    if not lore_dir.exists():
        lore_dir = Path(r"c:\Users\echov\Desktop\Kódenie\Elena\lore")
    
    if not lore_dir.exists():
        logger.error("❌ Lore directory not found!")
        return
    
    logger.info(f"📁 Using lore directory: {lore_dir.absolute()}")
    
    # Process all cards
    fixer = YAMLCardFixer()
    fixer.process_all_cards(lore_dir)
    
    logger.info("🎉 COMPLETE! All cards translated and fixed!")

if __name__ == "__main__":
    main()
