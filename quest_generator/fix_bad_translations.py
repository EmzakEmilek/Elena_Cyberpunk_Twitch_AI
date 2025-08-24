#!/usr/bin/env python3
"""
🚨 EMERGENCY FIX - Opraví zlé preklady
Opraví slovinčinu -> slovenčinu a mojibake
"""

import yaml
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationFixer:
    def __init__(self):
        # Slovenian -> Slovak fixes
        self.slovenian_fixes = {
            'naslov': 'názov',
            'ime': 'meno', 
            'spola': 'pohlavie',
            'frakcija': 'frakcia',
            'približenje': 'prístup',
            'sisteme': 'systémy',
            'príroda': 'povaha',
            'obydlie': 'bydlisko',
            'posobnosti': 'schopnosti',
            'slabosti': 'slabosti',
            'obdobi': 'obdobie',
            'možnosti': 'možnosti',
            'vplivy': 'vplyvy',
            'fokus': 'zameranie',
            'výkon': 'výkon',
            'oblast': 'oblasť',
            'sposobnosti': 'schopnosti',
            'približenie': 'prístup',
            'priamočasný': 'priamočiary',
            'pridružitev': 'pridruženie',
            'zavislosti': 'závislosti',
            'bivši': 'bývalý',
            'aktualný': 'aktuálny',
            'sistémy': 'systémy',
            'računovana': 'vypočítavaná',
            'oddelena': 'oddelená',
            'oddeljenje': 'oddelenie',
            'znad': 'za',
            'omrežja': 'siete',
            'zmăganie': 'ovládanie',
            'prekračovanie': 'prekračovanie',
            'obveznosti': 'povinnosti',
            'metódy': 'metódy',
            'celková': 'úplná',
            'ničiteľnost': 'ničivosť',
            'maximalna': 'maximálna',
            'nasilnost': 'násilnosť',
            'nezadržljiva': 'nezastaviteľná',
            'učinkovitost': 'účinnosť',
            'zameritev': 'zameranie',
            'zanítosť': 'zanietenie',
            'pohŕdavá': 'pohŕdavá',
            'obtor': 'oblasť',
            'priljevati': 'priľnúť'
        }
        
        # Mojibake fixes
        self.mojibake_fixes = {
            'preloĹľenĂ©': 'preložené',
            'termĂ­nmi': 'termínmi',
            'PouličnĂ©': 'Pouličné',
            'konverz': 'konverzácia',
            'ĹľenĂ©': 'žené'
        }
        
        self.files_fixed = 0
        self.total_fixes = 0
    
    def fix_text_recursive(self, obj):
        """Recursively fix text in data structure"""
        if isinstance(obj, str):
            original = obj
            fixed = obj
            
            # Fix Slovenian words
            for slo, svk in self.slovenian_fixes.items():
                pattern = r'\b' + re.escape(slo) + r'\b'
                fixed = re.sub(pattern, svk, fixed, flags=re.IGNORECASE)
            
            # Fix mojibake
            for wrong, correct in self.mojibake_fixes.items():
                fixed = fixed.replace(wrong, correct)
            
            # Remove prompt artifacts
            if 'PRAVIDLÁ:' in fixed or 'PRÍKLADY SPRÁVNEJ' in fixed:
                # Extract just the actual translation
                lines = fixed.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(keyword in line.upper() for keyword in [
                        'PRAVIDLÁ', 'PRÍKLADY', 'KONTEXT', 'TEXT NA PREKLAD', 
                        'SLOVENSKÝ PREKLAD', 'NIE SRBSKY', 'HELLO WORLD'
                    ]):
                        if len(line) > 3:  # Not just punctuation
                            fixed = line
                            break
            
            if fixed != original:
                self.total_fixes += 1
                logger.debug(f"FIXED: '{original[:50]}...' -> '{fixed[:50]}...'")
            
            return fixed
            
        elif isinstance(obj, dict):
            return {k: self.fix_text_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.fix_text_recursive(item) for item in obj]
        else:
            return obj
    
    def fix_card(self, file_path: Path):
        """Fix single card"""
        try:
            # Load
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            original_fixes = self.total_fixes
            
            # Fix all text
            fixed_data = self.fix_text_recursive(data)
            
            # Save if changes were made
            if self.total_fixes > original_fixes:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(fixed_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
                logger.info(f"✅ Fixed {file_path.name} - {self.total_fixes - original_fixes} corrections")
                self.files_fixed += 1
                return True
            else:
                logger.info(f"✅ {file_path.name} - no fixes needed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error fixing {file_path}: {e}")
            return False
    
    def fix_all_cards(self, lore_dir: Path):
        """Fix all cards"""
        logger.info("🚨 EMERGENCY TRANSLATION FIX - Starting...")
        
        yaml_files = list(lore_dir.rglob("*.yaml")) + list(lore_dir.rglob("*.yml"))
        
        # Focus on the three problematic cards first
        priority_files = [
            'adam_smasher.yaml',
            'alt_cunningham.yaml', 
            'jackie_welles.yaml'
        ]
        
        # Process priority files first
        for priority in priority_files:
            priority_path = None
            for file_path in yaml_files:
                if file_path.name == priority:
                    priority_path = file_path
                    break
            
            if priority_path:
                logger.info(f"🎯 PRIORITY FIX: {priority}")
                self.fix_card(priority_path)
        
        # Then process all others
        logger.info(f"🔄 Processing remaining {len(yaml_files) - len(priority_files)} files...")
        
        for file_path in yaml_files:
            if file_path.name not in priority_files:
                self.fix_card(file_path)
        
        logger.info("=" * 50)
        logger.info(f"✅ SUMMARY:")
        logger.info(f"   Files fixed: {self.files_fixed}")
        logger.info(f"   Total corrections: {self.total_fixes}")
        logger.info("🎉 Emergency fix complete!")

def main():
    lore_dir = Path("../lore")
    if not lore_dir.exists():
        lore_dir = Path("lore")
    if not lore_dir.exists():
        lore_dir = Path(r"c:\Users\echov\Desktop\Kódenie\Elena\lore")
    
    if not lore_dir.exists():
        logger.error("❌ Lore directory not found!")
        return
    
    fixer = TranslationFixer()
    fixer.fix_all_cards(lore_dir)

if __name__ == "__main__":
    main()
