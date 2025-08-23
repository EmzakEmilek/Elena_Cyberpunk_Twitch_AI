"""
Audio processor pre zachytávanie a spracovanie zvuku.
"""

from dataclasses import dataclass
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import threading
import logging
from datetime import datetime
from ..config.config import AudioConfig

logger = logging.getLogger(__name__)


@dataclass
class AudioState:
    is_recording: bool = False
    frames: list = None
    recording_start: Optional[float] = None

    def __post_init__(self):
        self.frames = []


class AudioProcessor:
    def __init__(self, config: AudioConfig, callback: Callable):
        """
        Inicializuje audio processor.

        Args:
            config: Konfigurácia pre audio zariadenie
            callback: Callback funkcia volaná pri nahratí nového audio framu
        """
        self.config = config
        self.callback = callback
        self.state = AudioState()
        self.stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def start_stream(self):
        """Spustí audio stream zo vstupného zariadenia."""
        try:
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                blocksize=self.config.blocksize,
                device=self.config.input_device_index,
                callback=self._audio_callback,
                dtype=np.float32,
            )
            self.stream.start()
            logger.info(
                f"Audio stream spustený (vzorkovanie: {self.config.sample_rate}Hz)"
            )
        except Exception as e:
            logger.error(f"Nepodarilo sa spustiť audio stream: {str(e)}")
            raise

    def stop_stream(self):
        """Zastaví audio stream."""
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
                logger.info("Audio stream zastavený")
            except Exception as e:
                logger.error(f"Chyba pri zastavovaní audio streamu: {str(e)}")
            finally:
                self.stream = None

    def start_recording(self):
        """Začne nahrávanie."""
        with self._lock:
            if not self.state.is_recording:
                self.state.is_recording = True
                self.state.recording_start = datetime.now().timestamp()
                self.state.frames = []
                logger.info("Nahrávanie spustené")

    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Zastaví nahrávanie a vráti nahrané audio data.

        Returns:
            Numpy array s audio dátami alebo None ak nie sú žiadne dáta
        """
        with self._lock:
            if self.state.is_recording:
                self.state.is_recording = False
                if not self.state.frames:
                    logger.warning("Žiadne audio dáta neboli nahraté")
                    return None

                audio = np.concatenate(self.state.frames, axis=0)
                duration = len(audio) / self.config.sample_rate
                logger.info(f"Nahrávanie ukončené (dĺžka: {duration:.1f}s)")
                return audio
            return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback volaný pri každom novom audio frame."""
        if status:
            logger.warning(f"Audio status: {status}")

        with self._lock:
            if self.state.is_recording:
                # Berieme len prvý kanál pre mono
                mono = indata[:, 0].copy()
                self.state.frames.append(mono)
                self.callback(mono)
