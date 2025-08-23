"""
Demo skript pre testovanie Azure TTS.
"""

import asyncio
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from src.services.tts.azure_tts import AzureTTS

# Načítaj .env súbor
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        start_time = time.time()
        logger.info("Inicializujem Azure TTS...")
        tts = AzureTTS()
        init_time = time.time() - start_time
        logger.info(f"Inicializácia dokončená za {init_time:.2f}s")

        text = "Ahoj, ja som Elena. Test jedna, dva, tri."
        
        logger.info("Spúšťam syntézu...")
        synth_start = time.time()
        boundaries = await tts.speak_async(text)
        synth_time = time.time() - synth_start
        
        logger.info(f"\nŠtatistiky syntézy:")
        logger.info(f"Celkový čas: {synth_time:.2f}s")
        logger.info(f"Dĺžka textu: {len(text)} znakov")
        logger.info(f"Počet slov: {len(boundaries)} slov")
        logger.info(f"Znakov za sekundu: {len(text)/synth_time:.1f}")
        
        logger.info(f"\nWord boundaries:")
        for b in boundaries:
            logger.info(f"  {b.time_ms}ms: {text[b.text_offset:b.text_offset + b.word_length]}")
        
        logger.info("\nDemo dokončené!")
        
    except Exception as e:
        logger.error(f"Chyba: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
