"""
Asynchrónna služba pre komunikáciu s OpenAI Assistant API.
"""

import asyncio
from openai import AsyncOpenAI
from typing import Optional
import time
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AssistantConfig:
    def __init__(self):
        """Inicializuje konfiguráciu asistenta."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.assistant_id = os.getenv("ASSISTANT_ID")
        self.thread_id_file = Path("thread_id.txt")
        self._thread_id = None

        if not self.api_key or not self.assistant_id:
            raise RuntimeError(
                "Chýbajú potrebné premenné prostredia - skontroluj OPENAI_API_KEY "
                "a ASSISTANT_ID v súbore .env."
            )

    @property
    def thread_id(self) -> Optional[str]:
        """Získa thread ID z cache alebo zo súboru."""
        if not self._thread_id:
            self._thread_id = self._load_thread_id()
        return self._thread_id

    def _load_thread_id(self) -> Optional[str]:
        """Načíta thread ID z disku ak existuje."""
        try:
            if self.thread_id_file.exists():
                tid = self.thread_id_file.read_text(encoding="utf-8").strip()
                if tid:
                    logger.info(f"Načítané uložené THREAD_ID: {tid}")
                    return tid
        except Exception as e:
            logger.warning(f"Chyba pri načítaní THREAD_ID zo súboru: {e}")
        return None

    def _save_thread_id(self, thread_id: str):
        """Uloží thread ID na disk."""
        try:
            self.thread_id_file.write_text(thread_id, encoding="utf-8")
            logger.info(f"Uložené THREAD_ID ({thread_id}) do {self.thread_id_file}")
        except Exception as e:
            logger.warning(f"Chyba pri ukladaní THREAD_ID do súboru: {e}")


class AssistantService:
    def __init__(self, config: AssistantConfig):
        """Inicializuje službu s konfiguráciou asistenta."""
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.assistant_id = config.assistant_id
        self._thread = None

    async def init_thread(self):
        """Inicializuje alebo vráti existujúce konverzačné vlákno."""
        if not self._thread:
            self._thread = await self.client.beta.threads.create()
            logger.info(f"Vytvorené nové konverzačné vlákno: {self._thread.id}")
        return self._thread

    async def get_response(
        self, author_name: str, user_input: str, max_retries: int = 2
    ) -> Optional[str]:
        """
        Získa odpoveď od OpenAI asistenta s retry logikou.

        Args:
            author_name: Meno autora správy
            user_input: Text od používateľa
            max_retries: Maximálny počet pokusov pri zlyhaní

        Returns:
            Odpoveď od asistenta alebo None v prípade chyby
        """
        backoff = 2.0
        for attempt in range(1, max_retries + 1):
            try:
                thread = await self.init_thread()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                prompt = f"[{timestamp}] [{author_name}]: {user_input}"

                logger.info(f"Odosielam správu do OpenAI (pokus {attempt}): {prompt}")

                # Pridaj správu do vlákna
                await self.client.beta.threads.messages.create(
                    thread_id=thread.id, role="user", content=prompt
                )

                # Spusti asistenta
                run = await self.client.beta.threads.runs.create(
                    thread_id=thread.id, assistant_id=self.assistant_id
                )

                # Čakaj na dokončenie s timeoutom
                start_time = time.perf_counter()
                while True:
                    run = await self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run.id
                    )
                    if run.status == "completed":
                        break
                    elif run.status in ["failed", "cancelled", "expired"]:
                        logger.error(f"Asistent zlyhal: {run.last_error}")
                        raise RuntimeError(f"Asistent zlyhal: {run.status}")
                    elif time.perf_counter() - start_time > 30:  # 30s timeout
                        logger.error("Timeout pri čakaní na odpoveď")
                        raise TimeoutError("Timeout pri čakaní na odpoveď")

                    await asyncio.sleep(0.5)

                # Získaj odpoveď
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )

                if not messages.data:
                    logger.warning("Prázdna odpoveď od asistenta")
                    return None

                response = messages.data[0].content[0].text.value
                logger.info(f"Prijatá odpoveď od asistenta: {response}")
                return response.strip()

            except Exception as e:
                logger.warning(
                    f"Pokus {attempt} pre {author_name} zlyhal: {str(e)}", exc_info=True
                )
                if attempt < max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    return "Prepáč, Elena má technický problém s OpenAI komunikáciou."

        return "Elena momentálne nemôže odpovedať."
