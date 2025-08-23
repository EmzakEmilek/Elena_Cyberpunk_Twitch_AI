"""
Hlavný spúšťací súbor pre Elena STT.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime
from src.core.elena import Elena


def setup_logging():
    """Nastaví základné logovanie."""
    # Vytvorenie formátovača pre súbor
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler pre súbor
    file_handler = logging.FileHandler(
        f"logs/elena_stt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    # Základné nastavenie
    logging.basicConfig(level=logging.INFO, handlers=[file_handler])


def main():
    # Vytvorenie logs priečinka ak neexistuje
    Path("logs").mkdir(exist_ok=True)

    # Nastavenie logovania
    setup_logging()
    logger = logging.getLogger(__name__)

    # Načítanie environment variables
    load_dotenv()

    # Kontrola environment variables
    required_vars = ["OPENAI_API_KEY", "ASSISTANT_ID"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Chýbajú potrebné environment variables: {', '.join(missing)}")
        sys.exit(1)

    try:
        # Spustenie aplikácie
        elena = Elena(Path("config.yaml"))
        elena.run()
    except KeyboardInterrupt:
        logger.info("Program ukončený používateľom")
    except Exception as e:
        logger.error(f"Neočakávaná chyba: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
