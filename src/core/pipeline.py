"""
Pipeline systém pre paralelné spracovanie audio vstupu, transkripcie a generovania odpovedí.
"""

import asyncio
from typing import Optional, Dict, Any
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from colorama import Fore, Style


@dataclass
class AudioSegment:
    """Reprezentuje segment audio dát na spracovanie"""

    audio: np.ndarray
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class TranscriptionResult:
    """Výsledok transkripcie"""

    text: str
    language: str
    language_probability: float
    segments: list
    timing: Dict[str, float]


@dataclass
class AssistantResponse:
    """Odpoveď od asistenta"""

    text: str
    timing: Dict[str, float]


class ProcessingPipeline:
    def __init__(self, model, assistant, max_workers=3):
        """
        Inicializuje pipeline pre paralelné spracovanie.

        Args:
            model: Whisper model pre transkripciu
            assistant: OpenAI asistent
            max_workers: Maximálny počet worker threadov
        """
        self.model = model
        self.assistant = assistant
        self.max_workers = max_workers

        # Fronty pre pipeline stages
        self.audio_queue = asyncio.Queue()
        self.transcription_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()

        # Thread pool pre CPU-intensive operácie
        self.thread_pool = []
        self.running = True

        # Event loop pre async operácie
        self.loop = asyncio.get_event_loop()

    def start(self):
        """Spustí pipeline a vytvorí worker thready"""
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._transcription_worker, daemon=True)
            thread.start()
            self.thread_pool.append(thread)

        # Spustí async task pre spracovanie odpovedí
        self.loop.create_task(self._process_responses())

    def stop(self):
        """Zastaví pipeline a cleanup"""
        self.running = False
        for _ in range(self.max_workers):
            self.audio_queue.put_nowait(None)  # sentinel

    async def process_audio(self, audio: np.ndarray, metadata: Dict[str, Any]):
        """
        Async metóda pre spracovanie audio segmentu.

        Args:
            audio: Audio dáta ako numpy array
            metadata: Metadáta o nahrávaní
        """
        segment = AudioSegment(audio=audio, timestamp=datetime.now(), metadata=metadata)
        await self.audio_queue.put(segment)

    def _transcription_worker(self):
        """Worker thread pre CPU-intensive transkripciu"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.running:
            try:
                segment = loop.run_until_complete(self.audio_queue.get())
                if segment is None:
                    break

                # Transkripcia (CPU-intensive)
                start_time = time.monotonic()
                segments, info = self.model.transcribe(
                    audio=segment.audio, **segment.metadata
                )
                transcription_ms = (time.monotonic() - start_time) * 1000

                full_text = " ".join(s.text.strip() for s in segments)

                result = TranscriptionResult(
                    text=full_text,
                    language=info.language,
                    language_probability=info.language_probability,
                    segments=list(segments),
                    timing={"transcription_ms": transcription_ms},
                )

                # Odošli výsledok do ďalšej fronty
                asyncio.run_coroutine_threadsafe(
                    self.transcription_queue.put(result), self.loop
                )

            except Exception as e:
                print(f"{Fore.RED}Chyba pri transkripcii: {e}{Style.RESET_ALL}")

        loop.close()

    async def _process_responses(self):
        """Async task pre spracovanie odpovedí od asistenta"""
        while self.running:
            try:
                # Čakaj na transkripciu
                result = await self.transcription_queue.get()

                if not result.text.strip():
                    continue

                # Získaj odpoveď od asistenta (I/O bound)
                start_time = time.monotonic()
                response_text, first_token_ms = await self.assistant.get_response_async(
                    "Používateľ", result.text
                )
                assistant_ms = (time.monotonic() - start_time) * 1000

                result.timing["first_token_ms"] = first_token_ms
                result.timing["assistant_ms"] = assistant_ms
                result.timing["total_ms"] = (
                    result.timing["transcription_ms"] + assistant_ms
                )

                # Odošli do fronty pre výpis
                await self.response_queue.put(
                    AssistantResponse(text=response_text, timing=result.timing)
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"{Fore.RED}Chyba pri generovaní odpovede: {e}{Style.RESET_ALL}")

    async def get_next_response(self) -> Optional[AssistantResponse]:
        """Získa ďalšiu dostupnú odpoveď z fronty"""
        try:
            return await self.response_queue.get()
        except queue.Empty:
            return None
