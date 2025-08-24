#!/usr/bin/env python3
"""
📚 CYBERPUNK DATA SCRAPER
Collects quest data from external sources for LLM generation
"""

import requests
import json
import yaml
from bs4 import BeautifulSoup
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CyberpunkDataScraper:
    """Scrapes Cyberpunk 2077 quest data from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data = {
            'quests': {},
            'characters': {},
            'locations': {},
            'items': {}
        }
    
    def scrape_cyberpunk_wiki(self):
        """Scrape quest data from Cyberpunk Wiki"""
        logger.info("🌐 Scraping Cyberpunk Wiki...")
        
        # Main quest categories URLs
        quest_urls = {
            'main_story': 'https://cyberpunk.fandom.com/wiki/Category:Main_Jobs_(Cyberpunk_2077)',
            'side_quests': 'https://cyberpunk.fandom.com/wiki/Category:Side_Jobs_(Cyberpunk_2077)',
            'gigs': 'https://cyberpunk.fandom.com/wiki/Category:Gigs_(Cyberpunk_2077)',
            'cyberpsycho': 'https://cyberpunk.fandom.com/wiki/Category:Cyberpsycho_Sightings'
        }
        
        for category, url in quest_urls.items():
            try:
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find quest links
                quest_links = soup.find_all('a', class_='category-page__member-link')
                
                for link in quest_links:
                    quest_name = link.get_text().strip()
                    quest_url = 'https://cyberpunk.fandom.com' + link.get('href')
                    
                    # Scrape individual quest page
                    quest_data = self._scrape_quest_page(quest_url, quest_name)
                    
                    if quest_data:
                        self.data['quests'][quest_name] = {
                            'category': category,
                            'url': quest_url,
                            **quest_data
                        }
                    
                    time.sleep(1)  # Rate limiting
                    
            except Exception as e:
                logger.error(f"Error scraping {category}: {e}")
    
    def _scrape_quest_page(self, url: str, quest_name: str) -> dict:
        """Scrape individual quest page"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            quest_data = {
                'name': quest_name,
                'description': '',
                'objectives': [],
                'characters': [],
                'locations': [],
                'rewards': [],
                'prerequisites': []
            }
            
            # Extract description from first paragraph
            first_p = soup.find('div', class_='mw-parser-output').find('p')
            if first_p:
                quest_data['description'] = first_p.get_text().strip()
            
            # Extract objectives
            objectives_section = soup.find('span', {'id': 'Objectives'})
            if objectives_section:
                objectives_list = objectives_section.find_next('ul')
                if objectives_list:
                    for li in objectives_list.find_all('li'):
                        quest_data['objectives'].append(li.get_text().strip())
            
            # Extract characters (from links)
            character_links = soup.find_all('a', href=lambda x: x and '/wiki/' in x and 'Character' not in x)
            for link in character_links:
                char_name = link.get_text().strip()
                if len(char_name) > 2 and char_name not in quest_data['characters']:
                    quest_data['characters'].append(char_name)
            
            return quest_data
            
        except Exception as e:
            logger.error(f"Error scraping quest {quest_name}: {e}")
            return None
    
    def scrape_reddit_data(self):
        """Scrape quest discussions from Reddit"""
        logger.info("🔍 Scraping Reddit discussions...")
        
        # Use Reddit API or web scraping for quest discussions
        # This would collect community insights and tips
        pass
    
    def extract_game_files(self):
        """Extract data from game files (if available)"""
        logger.info("🎮 Looking for game files...")
        
        # Common Cyberpunk 2077 installation paths
        game_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077",
            r"C:\Program Files\Epic Games\Cyberpunk 2077",
            r"C:\GOG Games\Cyberpunk 2077"
        ]
        
        for path in game_paths:
            game_dir = Path(path)
            if game_dir.exists():
                logger.info(f"🎯 Found game installation: {path}")
                
                # Look for localization files with quest data
                localization_dir = game_dir / "archive" / "pc" / "content"
                if localization_dir.exists():
                    logger.info("📄 Found localization files")
                    # Extract quest names and descriptions
                
                break
        else:
            logger.warning("❌ No game installation found")
    
    def save_data(self, output_file: str = "quest_generator/cyberpunk_data.json"):
        """Save collected data to JSON file"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Data saved to {output_file}")
        logger.info(f"📊 Collected {len(self.data['quests'])} quests")
    
    def create_quest_templates(self):
        """Create quest templates from collected data"""
        logger.info("📝 Creating quest templates...")
        
        templates = []
        for quest_name, quest_data in self.data['quests'].items():
            template = {
                'name': quest_name,
                'category': quest_data.get('category', 'unknown'),
                'description': quest_data.get('description', ''),
                'characters': quest_data.get('characters', []),
                'objectives': quest_data.get('objectives', []),
                'locations': quest_data.get('locations', [])
            }
            templates.append(template)
        
        # Save templates
        with open('quest_generator/quest_templates.json', 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Created {len(templates)} quest templates")

def main():
    """Main data collection function"""
    logger.info("🚀 Starting Cyberpunk data collection...")
    
    scraper = CyberpunkDataScraper()
    
    # Collect data from various sources
    scraper.scrape_cyberpunk_wiki()
    scraper.extract_game_files()
    
    # Save collected data
    scraper.save_data()
    scraper.create_quest_templates()
    
    logger.info("✅ Data collection completed!")

if __name__ == "__main__":
    main()
