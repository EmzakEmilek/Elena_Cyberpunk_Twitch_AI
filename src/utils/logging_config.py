"""
Konfigurácia logovania pre Elena STT.
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logging() -> logging.Logger:
    """
    Nastaví základné logovanie.

    Returns:
        Logger pre hlavný modul
    """
    # Vytvorenie logs priečinka
    Path("logs").mkdir(exist_ok=True)

    # Vytvorenie formátovača pre súbor
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler pre súbor
    log_file = f"logs/elena_stt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    # Základné nastavenie
    logging.basicConfig(level=logging.INFO, handlers=[file_handler])

    return logging.getLogger(__name__)
