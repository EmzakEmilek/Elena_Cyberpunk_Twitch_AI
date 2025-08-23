"""
Queue management pre TTS požiadavky.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from .azure_tts import TTSWordBoundary, AzureTTS

logger = logging.getLogger(__name__)


@dataclass
class TTSRequest:
    """Reprezentuje jednu TTS požiadavku vo fronte."""
    text: str
    priority: int = 0


class TTSQueue:
    """Správa fronty TTS požiadaviek."""

    def __init__(self, tts: AzureTTS, max_size: int = 10):
        """
        Inicializuje TTS queue.
        
        Args:
            tts: AzureTTS inštancia
            max_size: Maximálna veľkosť fronty
        """
        self.tts = tts
        self.max_size = max_size
        self.queue: asyncio.PriorityQueue[tuple[int, int, TTSRequest]] = asyncio.PriorityQueue(max_size)
        self.is_processing = False
        self._counter = 0  # Pre zachovanie FIFO poradia pri rovnakej priorite
        self._current_task: Optional[asyncio.Task] = None

    async def add(self, text: str, priority: int = 0) -> bool:
        """
        Pridá text do fronty.
        
        Args:
            text: Text na syntézu
            priority: Priorita (nižšie číslo = vyššia priorita)
            
        Returns:
            True ak bol text pridaný, False ak je fronta plná
        """
        if self.queue.full():
            logger.warning("TTS fronta je plná, správa zahodená")
            return False

        self._counter += 1
        request = TTSRequest(text=text, priority=priority)
        await self.queue.put((priority, self._counter, request))
        
        if not self.is_processing:
            self._current_task = asyncio.create_task(self.process_queue())
        
        return True

    async def process_queue(self):
        """Spracuje všetky požiadavky vo fronte."""
        self.is_processing = True
        
        try:
            while not self.queue.empty():
                _, _, request = await self.queue.get()
                try:
                    # Vytvoríme event pre sledovanie word boundaries
                    word_printed = asyncio.Event()
                    printed_text = []

                    async def handle_word_boundary(text: str, boundary: TTSWordBoundary):
                        """Callback pre spracovanie word boundary eventu."""
                        word = text[boundary.text_offset:boundary.text_offset + boundary.word_length]
                        printed_text.append(word)
                        print(f"{word} ", end="", flush=True)  # Pridáme medzeru za každé slovo
                        word_printed.set()

                    # Vytvoríme future pre dokončenie syntézy
                    synthesis_done = asyncio.Future()
                    
                    def on_synthesis_complete(evt):
                        synthesis_done.set_result(True)
                    
                    # Spustíme TTS s callbackmi
                    boundaries = await self.tts.speak_async(
                        request.text,
                        on_word_boundary=handle_word_boundary,
                        on_completed=on_synthesis_complete
                    )
                    
                    # Počkáme na dokončenie syntézy
                    await synthesis_done
                    
                except Exception as e:
                    logger.error(f"Chyba pri spracovaní TTS požiadavky: {e}")
                finally:
                    self.queue.task_done()
        finally:
            self.is_processing = False

    async def _display_timed_text(self, text: str, boundaries: list[TTSWordBoundary]):
        """
        Zobrazí text synchrónne s TTS časovaním.
        
        Args:
            text: Celý text na zobrazenie
            boundaries: List word boundary eventov
        """
        if not boundaries:
            return

        # Zoradíme boundaries podľa času
        boundaries.sort(key=lambda x: x.time_ms)
        
        # Pre každé slovo vypočítame čas čakania od predchádzajúceho
        last_time = 0
        for boundary in boundaries:
            # Vypočítame čas čakania
            wait_time = (boundary.time_ms - last_time) / 1000.0  # konverzia na sekundy
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Získame slovo z textu
            word = text[boundary.text_offset:boundary.text_offset + boundary.word_length]
            # Vypíšeme slovo
            print(word, end="", flush=True)
            
            last_time = boundary.time_ms

    async def flush(self):
        """Vyčistí frontu."""
        if self._current_task:
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
        
        while not self.queue.empty():
            try:
                await self.queue.get()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
