"""
Rozšírený konfiguračný systém s validáciou a dedičnosťou.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    """Konfigurácia pre Whisper model"""

    size: str = "medium"
    language: str = "sk"
    cuda_enabled: bool = True
    cuda_compute_type: str = "float16"
    cpu_compute_type: str = "int8"
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    vad_filter: bool = True
    no_speech_threshold: float = 0.6

    def validate(self):
        """Validuje konfiguráciu"""
        valid_sizes = [
            "tiny",
            "base",
            "small",
            "medium",
            "large-v1",
            "large-v2",
            "large-v3",
        ]
        if self.size not in valid_sizes:
            raise ValueError(
                f"Neplatná veľkosť modelu. "
                f"Povolené hodnoty: {', '.join(valid_sizes)}"
            )

        valid_compute = ["float16", "float32", "int8", "int16"]
        if self.cuda_compute_type not in valid_compute:
            raise ValueError(
                f"Neplatný compute type pre CUDA. "
                f"Povolené hodnoty: {', '.join(valid_compute)}"
            )

        if self.cpu_compute_type not in valid_compute:
            raise ValueError(
                f"Neplatný compute type pre CPU. "
                f"Povolené hodnoty: {', '.join(valid_compute)}"
            )


@dataclass
class AudioConfig:
    """Konfigurácia pre audio processing"""

    sample_rate: int = 16000
    channels: int = 1
    blocksize: int = 1024
    device_index: Optional[int] = None
    pre_roll_sec: float = 0.5
    post_roll_sec: float = 0.5

    # VAD
    vad_enabled: bool = True
    vad_threshold: float = 0.01
    vad_window: int = 10

    # Noise reduction
    noise_reduction: bool = True
    noise_floor: float = 0.1

    def validate(self):
        """Validuje konfiguráciu"""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate musí byť kladné číslo")

        if self.channels <= 0:
            raise ValueError("Počet kanálov musí byť kladné číslo")

        if self.blocksize <= 0:
            raise ValueError("Blocksize musí byť kladné číslo")

        if self.pre_roll_sec < 0:
            raise ValueError("Pre-roll čas nemôže byť záporný")

        if self.post_roll_sec < 0:
            raise ValueError("Post-roll čas nemôže byť záporný")


@dataclass
class UIConfig:
    """Konfigurácia pre používateľské rozhranie"""

    colors: Dict[str, str] = field(
        default_factory=lambda: {
            "primary": "cyan",
            "secondary": "magenta",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
        }
    )
    show_timings: bool = True
    show_device_info: bool = True
    show_language_info: bool = True
    clear_screen: bool = True
    emoji_enabled: bool = True


@dataclass
class SystemConfig:
    """Systémová konfigurácia"""

    thread_pool_size: int = 3
    enable_telemetry: bool = True
    metrics_file: str = "metrics.json"
    log_level: str = "INFO"
    memory_limit_mb: int = 1024

    def validate(self):
        """Validuje konfiguráciu"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(
                f"Neplatný log level. "
                f"Povolené hodnoty: {', '.join(valid_log_levels)}"
            )

        if self.thread_pool_size <= 0:
            raise ValueError("Thread pool size musí byť kladné číslo")

        if self.memory_limit_mb <= 0:
            raise ValueError("Memory limit musí byť kladné číslo")


class Config:
    """Hlavná konfiguračná trieda"""

    def __init__(
        self,
        whisper: WhisperConfig,
        audio: AudioConfig,
        ui: UIConfig,
        system: SystemConfig,
    ):
        self.whisper = whisper
        self.audio = audio
        self.ui = ui
        self.system = system

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Načíta konfiguráciu z YAML súboru"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Vytvor konfiguračné objekty
            whisper = WhisperConfig(**data.get("whisper", {}))
            audio = AudioConfig(**data.get("audio", {}))
            ui = UIConfig(**data.get("ui", {}))
            system = SystemConfig(**data.get("system", {}))

            # Validuj
            whisper.validate()
            audio.validate()
            system.validate()

            return cls(whisper, audio, ui, system)

        except Exception as e:
            logger.error(f"Chyba pri načítaní konfigurácie: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Konvertuje konfiguráciu na slovník"""
        return {
            "whisper": self.whisper.__dict__,
            "audio": self.audio.__dict__,
            "ui": self.ui.__dict__,
            "system": self.system.__dict__,
        }

    def save(self, path: Path):
        """Uloží konfiguráciu do súboru"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                if path.suffix == ".yaml":
                    yaml.dump(
                        self.to_dict(), f, default_flow_style=False, allow_unicode=True
                    )
                else:
                    json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Chyba pri ukladaní konfigurácie: {e}")
            raise
