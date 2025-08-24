#!/usr/bin/env python3
"""
🎯 PRECISION CARD STANDARDIZER
Senior developer approach - rule-based, precise, reliable
"""

import yaml
import re
from pathlib import Path
import logging
from typing import Dict, Any, List, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrecisionCardStandardizer:
    """Presný štandardizátor kariet bez AI chaos"""
    
    def __init__(self):
        # PERFECT PATTERNS z tých 6 opravených kariet
        self.slovenian_to_slovak = {
            # Základné slová
            'naslov': 'názov',
            'ime': 'meno',
            'spola': 'pohlavie', 
            'frakcija': 'frakcia',
            'rola': 'úloha',
            'patričnosť': 'príslušnosť',
            'pripojenie': 'príslušnosť',
            'pripojitev': 'príslušnosť',
            'skupnost': 'pohlavie',
            'spoločnosť': 'pohlavie',
            'bydlišťo': 'bydlisko',
            'obydlie': 'bydlisko',
            
            # Charakteristiky
            'vlastnosti': 'vlastnosti',  # správne
            'lastnosti': 'vlastnosti',
            'sily': 'schopnosti',
            'možnosti': 'schopnosti',
            'preferencie': 'slabosti',
            'slabosti': 'slabosti',  # správne
            
            # Rodinné vzťahy
            'závislosť': 'vzťah',
            'závislosti': 'vzťahy',
            'patričnosť': 'príslušnosť',
            
            # Miesta
            'nocné mesto': 'Night City',
            'severný dub': 'North Oak',
            'el kojot slepý': 'El Coyote Cojo',
            'zadaj za črnomu zídkom': 'za Blackwall',
            
            # Osobnosti
            'adam zmätkár': 'Adam Smasher',
            'starý cunninghama': 'Alt Cunningham',
            'starý cunninghame': 'Alt Cunningham',
            'judita álvarez': 'Judy Alvarez',
            
            # Zlé preklady osobnosti
            'strachovité': 'bezohľadný',
            'zakotrlačka': 'zamestnávateľ',
            'bivší': 'bývalý',
            'aktuálny': 'súčasný',
            'neustálý': 'náladový',
            'umelcoká': 'umelecká',
            'žiacka': 'žena',
            'mokša': 'Moxes',
            'mok': 'Moxes',
            
            # Deskripcie
            'záver': 'súhrn',
            'koniec': 'súhrn',
            'nadpis': 'názov',
            'cieľ': 'súhrn',
            
            # Organizácie
            'arasakova rodina': 'Arasaka rodina',
            'spoločnosť arasaka': 'Arasaka Corporation',
            
            # Status
            'deceased': 'mŕtvy',
            'alive': 'žije',
            'poznámky': 'poznámky',  # správne
            
            # Motivácie a role
            'perzekúcia': 'násilie',
            'sloboda': 'sloboda',  # správne
            'archetyp': 'archetyp',  # správne
            'motivácia': 'motivácia',  # správne
            
            # Technické
            'braindansa': 'braindance',
            'systémovia': 'systémy',
            'premeny': 'premeny',  # správne
            
            # Lokácie príbeh
            'záloha 1': 'Akt 1',
            'diela 2': 'Akt 2',
            'končna izkušnja': 'finálna výzva',
            'strachovský faktor': 'faktor strachu'
        }
        
        # Fixujeme encoding problémy
        self.mojibake_fixes = {
            'Ă˝': 'ý', 'ĂŤ': 'í', 'Ăˇ': 'á', 'Ă´': 'ô',
            'ĹĄ': 'š', 'Ĺ˝': 'ž', 'ĂŤ': 'é', 'ĹĽ': 'ť',
            'ÄŤ': 'č', 'Äť': 'Č',
            'preloĹľenĂ©': 'preložené',
            'termĂ­nmi': 'termínmi',
            'pouličnĂ©': 'pouličné'
        }
        
        # ŠTANDARD ŠTRUKTÚRY (z perfektných kariet)
        self.standard_structure = {
            'type': 'character',
            'id': 'char_*',
            'title': '',
            'aliases': [],
            'category': 'character_major',
            'lang': 'sk',
            'content': {
                'názov': '',
                'obsah': {'súhrn': ''},
                'meno': '',
                'príslušnosť': '',
                'personal_data': {
                    'úloha': '',
                    'pohlavie': '',
                    'bydlisko': '',
                    'frakcia': ''
                },
                'character_profile': {
                    'archetyp': '',
                    'motivácia': '',
                    'osobnosť': {
                        'vlastnosti': [],
                        'schopnosti': [],
                        'slabosti': []
                    }
                }
            },
            'meta': {
                'last_updated': '2025-08-24',
                'translation_status': 'manually_standardized',
                'source': 'Cyberpunk 2077 Fandom Wiki'
            }
        }
        
        self.processed = 0
        self.fixed = 0
        self.errors = 0
    
    def clean_text(self, text: str) -> str:
        """Vyčistí text od všetkých problémov"""
        if not isinstance(text, str):
            return text
        
        cleaned = text
        
        # 1. Fix mojibake
        for wrong, correct in self.mojibake_fixes.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # 2. Fix slovenian -> slovak
        for slo, svk in self.slovenian_to_slovak.items():
            # Case insensitive replacement
            pattern = re.compile(re.escape(slo), re.IGNORECASE)
            cleaned = pattern.sub(svk, cleaned)
        
        # 3. Remove AI prompt artifacts
        if any(keyword in cleaned for keyword in ['PRAVIDLÁ:', 'PRÍKLADY', 'KONTEXT:', 'PREKLAD:']):
            lines = cleaned.split('\n')
            for line in lines:
                line = line.strip()
                if (line and len(line) > 5 and 
                    not any(bad in line.upper() for bad in [
                        'PRAVIDLÁ', 'PRÍKLADY', 'KONTEXT', 'PREKLAD', 
                        'SLOVENSKÝ', 'SRBSKY', 'CHORVÁTSKY'
                    ])):
                    cleaned = line
                    break
        
        return cleaned.strip()
    
    def fix_recursive(self, obj: Any) -> Any:
        """Recursively fix všetky stringy v strukture"""
        if isinstance(obj, str):
            return self.clean_text(obj)
        elif isinstance(obj, dict):
            return {self.clean_text(k): self.fix_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.fix_recursive(item) for item in obj]
        else:
            return obj
    
    def standardize_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Štandardizuje štruktúru podľa perfect template"""
        
        # Start with clean standard
        result = {
            'type': 'character',
            'id': data.get('id', 'char_unknown'),
            'title': '',
            'aliases': [],
            'category': data.get('category', 'character_major'),
            'lang': 'sk',
            'content': {},
            'meta': {
                'last_updated': '2025-08-24',
                'translation_status': 'precision_standardized',
                'source': 'Cyberpunk 2077 Fandom Wiki'
            }
        }
        
        # Extract content safely
        content = data.get('content', {})
        
        # Detect main name/title
        name = (content.get('názov') or content.get('meno') or 
                content.get('name') or content.get('title') or 
                data.get('title', 'Unknown'))
        
        result['title'] = name
        result['content']['názov'] = name
        result['content']['meno'] = name
        
        # Extract summary
        summary_sources = [
            content.get('obsah', {}).get('súhrn'),
            content.get('obsah', {}).get('summary'),
            content.get('summary'),
            content.get('súhrn')
        ]
        summary = next((s for s in summary_sources if s and isinstance(s, str) and len(s) > 10), '')
        
        if summary:
            result['content']['obsah'] = {'súhrn': summary}
        
        # Copy other important fields
        if 'príslušnosť' in content or 'affiliation' in content:
            result['content']['príslušnosť'] = content.get('príslušnosť') or content.get('affiliation')
        
        # Personal data
        personal = content.get('personal_data', {})
        if personal:
            result['content']['personal_data'] = {
                'úloha': personal.get('úloha') or personal.get('role'),
                'pohlavie': personal.get('pohlavie') or personal.get('gender'),
                'bydlisko': personal.get('bydlisko') or personal.get('residence'),
                'frakcia': personal.get('frakcia') or personal.get('faction')
            }
        
        # Character profile
        profile = content.get('character_profile', {})
        if profile:
            result['content']['character_profile'] = {
                'archetyp': profile.get('archetyp') or profile.get('archetype'),
                'motivácia': profile.get('motivácia') or profile.get('motivation'),
                'osobnosť': profile.get('osobnosť') or profile.get('personality', {})
            }
        
        # Copy remaining fields
        for key, value in content.items():
            if key not in ['názov', 'meno', 'obsah', 'príslušnosť', 'personal_data', 'character_profile']:
                result['content'][key] = value
        
        return result
    
    def process_card(self, file_path: Path) -> bool:
        """Process single card with precision"""
        try:
            # Load
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            original = json.dumps(data, sort_keys=True, ensure_ascii=False)
            
            # 1. Fix all text issues
            clean_data = self.fix_recursive(data)
            
            # 2. Standardize structure
            standard_data = self.standardize_structure(clean_data)
            
            # Check if changes made
            final = json.dumps(standard_data, sort_keys=True, ensure_ascii=False)
            
            if final != original:
                # Save with backup
                backup_path = file_path.with_suffix('.yaml.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                
                # Save standardized
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(standard_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
                self.fixed += 1
                logger.info(f"✅ FIXED: {file_path.name}")
                return True
            else:
                logger.info(f"✅ OK: {file_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ ERROR {file_path.name}: {e}")
            self.errors += 1
            return False
    
    def process_batch(self, lore_dir: Path, batch_size: int = 10, preview: bool = True) -> None:
        """Process cards in batches with preview"""
        
        yaml_files = list(lore_dir.rglob("*.yaml")) + list(lore_dir.rglob("*.yml"))
        total = len(yaml_files)
        
        logger.info(f"🎯 PRECISION STANDARDIZER")
        logger.info(f"📁 Found {total} cards to process")
        logger.info(f"🔧 Batch size: {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = yaml_files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"\n📦 BATCH {batch_num}/{total_batches} ({len(batch)} files)")
            
            if preview:
                logger.info("🔍 PREVIEW mode - showing first 3 files:")
                for j, file_path in enumerate(batch[:3]):
                    # Show what would be changed
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        
                        if data and data.get('content'):
                            content = data['content']
                            title = (content.get('názov') or content.get('meno') or 
                                   content.get('name') or file_path.stem)
                            logger.info(f"   {j+1}. {title} ({file_path.name})")
                    except:
                        logger.info(f"   {j+1}. {file_path.name}")
                
                confirm = input(f"\n🤔 Process this batch? (y/n/s=skip): ").lower()
                if confirm == 'n':
                    logger.info("❌ Stopping...")
                    break
                elif confirm == 's':
                    logger.info("⏩ Skipping batch...")
                    continue
            
            # Process batch
            for file_path in batch:
                if self.process_card(file_path):
                    pass  # Already logged
                self.processed += 1
            
            logger.info(f"📊 Batch {batch_num} complete: {self.fixed} fixed, {self.errors} errors")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("🎉 PRECISION STANDARDIZATION COMPLETE!")
        logger.info(f"📁 Total processed: {self.processed}")
        logger.info(f"✅ Successfully fixed: {self.fixed}")
        logger.info(f"❌ Errors: {self.errors}")
        logger.info(f"📊 Success rate: {((self.processed - self.errors) / self.processed * 100):.1f}%")

def main():
    """Main function with user control"""
    print("🎯 PRECISION CARD STANDARDIZER")
    print("=" * 50)
    print("Senior developer approach:")
    print("✅ Rule-based (no AI chaos)")
    print("✅ Batch processing with preview")
    print("✅ Automatic backups")
    print("✅ Quality control")
    
    lore_dir = Path("../lore")
    if not lore_dir.exists():
        lore_dir = Path("lore")
    if not lore_dir.exists():
        lore_dir = Path(r"c:\Users\echov\Desktop\Kódenie\Elena\lore")
    
    if not lore_dir.exists():
        print("❌ Lore directory not found!")
        return
    
    print(f"\n📁 Using: {lore_dir.absolute()}")
    
    standardizer = PrecisionCardStandardizer()
    
    # Ask for batch size
    try:
        batch_size = int(input("\n🔢 Batch size (default 10): ") or "10")
    except:
        batch_size = 10
    
    # Ask for preview mode
    preview = input("🔍 Preview mode? (Y/n): ").lower() != 'n'
    
    standardizer.process_batch(lore_dir, batch_size, preview)

if __name__ == "__main__":
    main()
