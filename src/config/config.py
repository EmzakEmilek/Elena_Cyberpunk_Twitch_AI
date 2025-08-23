"""
Konfiguračný modul pre Elena STT.
Obsahuje všetky konfiguračné triedy a metódy pre načítanie konfigurácie.
"""

from dataclasses import dataclass
from typing import Optional
import yaml
from pathlib import Path


@dataclass
class ModelConfig:
    size: str
    language: str
    cuda_enabled: bool
    cuda_compute_type: str
    cpu_compute_type: str
    beam_size: int
    best_of: int
    temperature: float
    vad_filter: bool
    no_speech_threshold: float


@dataclass
class AudioConfig:
    sample_rate: int
    channels: int
    blocksize: int
    pre_roll_sec: float
    post_roll_sec: float
    input_device_index: Optional[int]


@dataclass
class ControlsConfig:
    ptt_key: str
    print_partials: bool


@dataclass
class AppConfig:
    model: ModelConfig
    audio: AudioConfig
    controls: ControlsConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Načíta konfiguráciu z YAML súboru."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        model = ModelConfig(
            size=data["model"]["size"],
            language=data["model"]["language"],
            cuda_enabled=data["model"]["cuda"]["enabled"],
            cuda_compute_type=data["model"]["cuda"]["compute_type"],
            cpu_compute_type=data["model"]["cpu"]["compute_type"],
            beam_size=data["model"]["inference"]["beam_size"],
            best_of=data["model"]["inference"]["best_of"],
            temperature=data["model"]["inference"]["temperature"],
            vad_filter=data["model"]["inference"]["vad_filter"],
            no_speech_threshold=data["model"]["inference"]["no_speech_threshold"],
        )

        audio = AudioConfig(
            sample_rate=data["audio"]["sample_rate"],
            channels=data["audio"]["channels"],
            blocksize=data["audio"]["blocksize"],
            pre_roll_sec=data["audio"]["pre_roll_sec"],
            post_roll_sec=data["audio"]["post_roll_sec"],
            input_device_index=data["audio"]["input_device_index"],
        )

        controls = ControlsConfig(
            ptt_key=data["controls"]["ptt_key"],
            print_partials=data["controls"]["print_partials"],
        )

        return cls(model=model, audio=audio, controls=controls)
