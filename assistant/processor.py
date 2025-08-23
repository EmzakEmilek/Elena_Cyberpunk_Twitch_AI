"""
Modul pre komunikáciu s OpenAI Assistant API.
"""

import os
import logging
import openai
from datetime import datetime
from typing import Optional

class AssistantConfig:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.assistant_id = os.getenv("ASSISTANT_ID")
        self.thread_id_file = "thread_id.txt"
        self._thread_id = None

    @property
    def thread_id(self) -> Optional[str]:
        if not self._thread_id:
            self._thread_id = self._load_thread_id()
        return self._thread_id

    def _load_thread_id(self) -> Optional[str]:
        """Načíta thread ID z disku ak existuje."""
        try:
            if os.path.exists(self.thread_id_file):
                with open(self.thread_id_file, "r", encoding="utf-8") as f:
                    tid = f.read().strip()
                    if tid:
                        logging.info(f"Načítané uložené THREAD_ID: {tid}")
                        return tid
        except Exception as e:
            logging.warning(f"Chyba pri načítaní THREAD_ID zo súboru: {e}")
        return None

    def _save_thread_id(self, thread_id: str):
        """Uloží thread ID na disk."""
        try:
            with open(self.thread_id_file, "w", encoding="utf-8") as f:
                f.write(thread_id)
            logging.info(f"Uložené THREAD_ID ({thread_id}) do {self.thread_id_file}")
        except Exception as e:
            logging.warning(f"Chyba pri ukladaní THREAD_ID do súboru: {e}")

class AssistantProcessor:
    def __init__(self, config: AssistantConfig):
        self.config = config
        self.validate_config()
        openai.api_key = self.config.api_key

    def validate_config(self):
        """Overí potrebnú konfiguráciu."""
        if not self.config.api_key or not self.config.assistant_id:
            raise RuntimeError(
                "Chýbajú potrebné premenné prostredia - skontroluj OPENAI_API_KEY "
                "a ASSISTANT_ID v súbore .env."
            )

    def create_thread(self) -> str:
        """Vytvorí nové OpenAI vlákno."""
        try:
            logging.info("Vytváram nové OpenAI vlákno...")
            thread = openai.beta.threads.create()
            self.config._thread_id = thread.id
            self.config._save_thread_id(thread.id)
            logging.info(f"Vytvorené nové OpenAI vlákno s ID: {thread.id}")
            return thread.id
        except Exception as e:
            logging.critical(
                f"Nepodarilo sa vytvoriť OpenAI vlákno: {e}. Skript nemôže pokračovať bez vlákna.",
                exc_info=True
            )
            raise RuntimeError(f"Nepodarilo sa vytvoriť OpenAI vlákno: {e}")

    def get_or_create_thread(self) -> str:
        """Získa existujúce thread ID alebo vytvorí nové."""
        if self.config.thread_id:
            return self.config.thread_id
        return self.create_thread()

    def get_response(self, author_name: str, user_query: str, max_retries: int = 2) -> str:
        """Získa odpoveď od OpenAI Assistant s logikou opakovania."""
        backoff = 2.0
        for attempt in range(1, max_retries + 1):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                prompt = f"[{timestamp}] [{author_name}]: {user_query}"
                
                # Vytvorenie správy vo vlákne
                thread_id = self.get_or_create_thread()
                openai.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=prompt
                )
                logging.info(f"Odoslané do OpenAI: {prompt}")

                # Spustenie asistenta
                run = openai.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.config.assistant_id
                )
                
                # Čakanie na dokončenie
                while True:
                    run_status = openai.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    if run_status.status == "completed":
                        # Získanie správ
                        messages = openai.beta.threads.messages.list(thread_id=thread_id)
                        if not messages.data:
                            return ""
                        latest_message = messages.data[0].content[0].text.value
                        return latest_message.strip()
                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        logging.error(f"Beh asistenta zlyhal: {run_status.status}")
                        break
                    
            except Exception as e:
                logging.warning(
                    f"Pokus {attempt} pre {author_name} zlyhal: {e}", exc_info=True
                )
                if attempt < max_retries:
                    backoff *= 2
                else:
                    return "Prepáč, Elena má technický problém s OpenAI komunikáciou."
            
        return "Elena momentálne nemôže odpovedať."
