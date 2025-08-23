"""
Hlavná trieda aplikácie Elena STT.

Táto trieda predstavuje jadro aplikácie Elena STT, ktorá zabezpečuje:
- Spracovanie hlasového vstupu
- Transkripciu pomocou Whisper modelu
- Komunikáciu s OpenAI                     # Spustenie TTS ak je k dispozícii
                    if self.tts_queue:
                        try:
                            # Odstránime emoji z textu pre TTS
                            import re
                            text_without_emoji = re.sub(r'[\U0001F000-\U0001F9FF]', '', response)
                            await self.tts_queue.add(text_without_emoji.strip())
                        except Exception as e:
                            logger.error(f"Chyba pri TTS: {e}")m
- Interaktívne používateľské rozhranie
"""

import asyncio
from pathlib import Path
from typing import Optional
import logging
import time
from datetime import datetime
from colorama import init, Fore, Style
from ..config.config import AppConfig
from ..services.assistant import AssistantService, AssistantConfig
from ..services.audio_processor import AudioProcessor
from ..utils.keyboard_listener import KeyboardListener
from ..services.tts.azure_tts import AzureTTS, TTSError
from ..services.tts.tts_queue import TTSQueue
from faster_whisper import WhisperModel
import numpy as np

# Inicializácia colorama pre Windows
init()

logger = logging.getLogger(__name__)


class Elena:
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Vyčistí text pre TTS - odstráni timestamp, [Elena] prefix a emoji.
        
        Args:
            text: Text na vyčistenie
            
        Returns:
            Vyčistený text
        """
        import re
        # Odstráni timestamp a [Elena] prefix
        clean_text = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[Elena\]: ', '', text)
        # Odstráni emoji
        clean_text = re.sub(r'[\U0001F000-\U0001F9FF]', '', clean_text)
        return clean_text.strip()

    def __init__(self, config_path: Path):
        """
        Inicializuje Elena STT.

        Args:
            config_path: Cesta ku konfiguračnému YAML súboru
        """
        self.config = AppConfig.from_yaml(config_path)
        self.assistant: Optional[AssistantService] = None
        self.audio: Optional[AudioProcessor] = None
        self.keyboard_listener: Optional[KeyboardListener] = None
        self.tts: Optional[AzureTTS] = None
        self.tts_queue: Optional[TTSQueue] = None
        self.loop = asyncio.new_event_loop()
        self.model: Optional[WhisperModel] = None
        self._setup_logging()

    def _setup_logging(self):
        """Nastaví logovanie."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def initialize(self):
        """Inicializuje všetky služby."""
        try:
            # Inicializácia OpenAI asistenta
            assistant_config = AssistantConfig()
            self.assistant = AssistantService(assistant_config)
            logger.info("OpenAI Assistant API inicializované")

            # Inicializácia audio procesora
            self.audio = AudioProcessor(
                config=self.config.audio, callback=self._handle_audio
            )
            logger.info("Audio processor inicializovaný")

            # Inicializácia Whisper modelu
            logger.info(f"Načítavam Whisper model: {self.config.model.size}")
            self.model = self._load_whisper_model()
            logger.info("Whisper model načítaný")

            # Nastavenie klávesových skratiek
            self._setup_keyboard_listener()
            logger.info("Klávesové skratky nastavené")

            # Inicializácia TTS ak je povolené
            if self.config.tts.enabled:
                try:
                    self.tts = AzureTTS(voice=self.config.tts.voice)
                    self.tts_queue = TTSQueue(
                        tts=self.tts,
                        max_size=self.config.tts.queue_max_size
                    )
                    logger.info("TTS inicializované")
                except TTSError as e:
                    logger.error(f"TTS inicializácia zlyhala: {e}")
                    logger.info("Prepínam na text-only mód")
                    self.tts = None
                    self.tts_queue = None

        except Exception as e:
            logger.error(f"Chyba pri inicializácii: {str(e)}")
            raise

    def _load_whisper_model(self) -> WhisperModel:
        """Načíta a inicializuje Whisper model."""
        if self.config.model.cuda_enabled:
            try:
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError("CUDA nie je dostupná")

                logger.info("Inicializujem Whisper na CUDA...")
                return WhisperModel(
                    self.config.model.size,
                    device="cuda",
                    compute_type=self.config.model.cuda_compute_type,
                )
            except Exception as e:
                logger.error(f"CUDA zlyhala: {str(e)}")
                logger.info("Prepínam na CPU")

        return WhisperModel(
            self.config.model.size,
            device="cpu",
            compute_type=self.config.model.cpu_compute_type,
        )

    def _setup_keyboard_listener(self):
        """Nastaví listener pre klávesové skratky."""
        self.keyboard_listener = KeyboardListener(
            ptt_key=self.config.controls.ptt_key,
            on_press_callback=self._start_recording_ui,
            on_release_callback=self._stop_recording_and_process,
        )
        self.keyboard_listener.start()

    def _start_recording_ui(self):
        """UI akcia pri začiatku nahrávania."""
        self.audio.start_recording()
        print("\033[2K\r", end="")  # Vyčisti riadok
        print(f"{Fore.RED}● NAHRÁVAM...{Style.RESET_ALL}", end="\r")
        logger.info(f"Nahrávam... ({datetime.now().strftime('%H:%M:%S')})")

    def _stop_recording_and_process(self):
        """UI akcia a spracovanie po skončení nahrávania."""
        print("\033[2K\r", end="")
        audio_data = self.audio.stop_recording()
        if audio_data is not None:
            asyncio.run_coroutine_threadsafe(self._process_audio(audio_data), self.loop)

    def _handle_audio(self, audio_data: np.ndarray):
        """Callback pre spracovanie audio dát."""
        # Tu môžeme pridať real-time spracovanie ak potrebujeme
        pass

    async def _process_audio(self, audio_data: np.ndarray):
        """
        Spracuje audio data - transkripcia a získanie odpovede.

        Args:
            audio_data: Audio dáta ako numpy array
        """
        try:
            # Čistenie obrazovky pre nové spracovanie
            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top

            # Meranie času
            process_start = time.perf_counter()
            transcription_start = time.perf_counter()

            print(f"\n{Fore.YELLOW}⌛ Prebieha transkripcia...{Style.RESET_ALL}")

            # Transkripcia
            segments, info = self.model.transcribe(
                audio=audio_data,
                language=self.config.model.language,
                beam_size=self.config.model.beam_size,
                best_of=self.config.model.best_of,
                temperature=self.config.model.temperature,
                vad_filter=self.config.model.vad_filter,
                no_speech_threshold=self.config.model.no_speech_threshold,
            )

            # Spracovanie segmentov
            text = " ".join(segment.text.strip() for segment in segments)
            transcription_end = time.perf_counter()
            transcription_time = transcription_end - transcription_start

            if text:
                logger.info(f"Transkripcia: {text}")
                logger.info(f"Čas transkripcie: {transcription_time:.1f}s")

                # Čistý výpis transkripcie
                print(
                    f"\n{Fore.CYAN}❝ {Style.BRIGHT}{text}{Style.RESET_ALL}{Fore.CYAN} ❞{Style.RESET_ALL}"
                )

                # Získanie odpovede od asistenta
                print(
                    f"\n{Fore.YELLOW}⌛ Generujem odpoveď od Eleny...{Style.RESET_ALL}"
                )
                assistant_start = time.perf_counter()
                response = await self.assistant.get_response("Používateľ", text)
                assistant_end = time.perf_counter()
                assistant_time = assistant_end - assistant_start
                total_time = assistant_end - process_start

                if response:
                    # Jednoduchý výpis odpovede
                    print(f"\n{Fore.MAGENTA}Elena: {Style.BRIGHT}{response}{Style.RESET_ALL}")

                    # Spustenie TTS ak je k dispozícii
                    if self.tts_queue:
                        try:
                            clean_text = self._clean_text_for_tts(response)
                            await self.tts_queue.add(clean_text)
                        except Exception as e:
                            logger.error(f"Chyba pri TTS: {e}")

                    # Výpis štatistík v kompaktnom formáte
                    print(f"\n{Fore.BLUE}━━━ Štatistiky ━━━{Style.RESET_ALL}")

                    # Farebné kódovanie časov
                    trans_color = (
                        Fore.GREEN
                        if transcription_time < 2.0
                        else (Fore.YELLOW if transcription_time < 4.0 else Fore.RED)
                    )
                    assist_color = (
                        Fore.GREEN
                        if assistant_time < 3.0
                        else (Fore.YELLOW if assistant_time < 6.0 else Fore.RED)
                    )
                    total_color = (
                        Fore.GREEN
                        if total_time < 5.0
                        else (Fore.YELLOW if total_time < 8.0 else Fore.RED)
                    )

                    print(
                        f"  • Transkripcia: {trans_color}{transcription_time:.1f}s{Style.RESET_ALL}"
                    )
                    print(
                        f"  • Odpoveď: {assist_color}{assistant_time:.1f}s{Style.RESET_ALL}"
                    )
                    print(
                        f"  • Celkový čas: {total_color}{total_time:.1f}s{Style.RESET_ALL}"
                    )

                    if info.language_probability > 0.9:
                        print(
                            f"  • Jazyk: {Fore.GREEN}{info.language}{Style.RESET_ALL}"
                        )
                    else:
                        print(
                            f"  • Jazyk: {Fore.YELLOW}{info.language} ({info.language_probability:.0%}){Style.RESET_ALL}"
                        )

                    print(
                        f"\n{Fore.CYAN}Stlač F12 pre ďalšie nahrávanie...{Style.RESET_ALL}"
                    )

                    logger.info(f"Odpoveď: {response}")
                    logger.info(f"Čas odpovede: {assistant_time:.1f}s")
                    logger.info(f"Celkový čas: {total_time:.1f}s")
            else:
                logger.warning("Nezachytený žiadny text")
                print(f"\n{Fore.YELLOW}⚠️ Nezachytený žiadny text{Style.RESET_ALL}")

        except Exception as e:
            logger.error(f"Chyba pri spracovaní audia: {str(e)}")
            print(f"\n{Fore.RED}❌ Chyba pri spracovaní: {str(e)}{Style.RESET_ALL}")

    async def _shutdown(self):
        """Graceful shutdown všetkých služieb."""
        if self.audio:
            self.audio.stop_stream()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.tts_queue:
            await self.tts_queue.flush()
        self.loop.close()

    def run(self):
        """Spustí hlavnú slučku aplikácie."""
        try:
            print("\033[2J\033[H", end="")  # Clear screen
            print(
                f"\n{Fore.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}┃{Style.RESET_ALL}           {Fore.WHITE}{Style.BRIGHT}Elena STT v2.0{Style.RESET_ALL}             {Fore.CYAN}┃{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Style.RESET_ALL}\n"
            )

            print(f"{Fore.YELLOW}⌛ Inicializujem služby...{Style.RESET_ALL}")

            # Inicializácia
            self.loop.run_until_complete(self.initialize())

            # Spustenie audio streamu
            self.audio.start_stream()
            logger.info("Elena je pripravená (F12 pre nahrávanie)")

            # Vyčisti obrazovku a zobraz úvodné info
            print("\033[2J\033[H", end="")
            print(
                f"\n{Fore.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}┃{Style.RESET_ALL}           {Fore.WHITE}{Style.BRIGHT}Elena STT v2.0{Style.RESET_ALL}             {Fore.CYAN}┃{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Style.RESET_ALL}\n"
            )

            print(f"{Fore.GREEN}✓ Systém je pripravený{Style.RESET_ALL}")
            print(f"\n{Fore.WHITE}Použitie:{Style.RESET_ALL}")
            print(
                f"  • Stlač a drž {Fore.CYAN}{Style.BRIGHT}[{self.config.controls.ptt_key.upper()}]{Style.RESET_ALL} pre nahrávanie"
            )
            print(
                f"  • Pusti {Fore.CYAN}{Style.BRIGHT}[{self.config.controls.ptt_key.upper()}]{Style.RESET_ALL} pre prepis"
            )
            print(
                f"  • Stlač {Fore.CYAN}{Style.BRIGHT}[Ctrl+C]{Style.RESET_ALL} pre ukončenie\n"
            )

            # Hlavná slučka
            self.loop.run_forever()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 Ukončujem program...{Style.RESET_ALL}")
            logger.info("Program ukončený používateľom")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Neočakávaná chyba: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Neočakávaná chyba: {str(e)}")
        finally:
            # Graceful shutdown
            self.loop.run_until_complete(self._shutdown())
