import logging
import time
from typing import Optional, Dict, Any, List, Iterator, Tuple
import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment, TranscriptionInfo
from dataclasses import dataclass

@dataclass
class WhisperConfig:
    """Configuration for Whisper model and inference."""
    model_name: str
    language: str
    use_cuda: bool
    cuda_compute_type: str
    cpu_compute_type: str
    beam_size: int
    best_of: int
    temperature: float
    vad_filter: bool
    no_speech_threshold: float

class STTProcessor:
    """Speech-to-text processor using Faster-Whisper."""
    
    def __init__(self, config: WhisperConfig):
        """Initialize the STT processor with configuration."""
        self.config = config
        self.logger = logging.getLogger("elena_stt")
        self.model: Optional[WhisperModel] = None
        self.device_kind: Optional[str] = None

    def initialize(self) -> None:
        """Initialize the Whisper model with CUDA or CPU."""
        self.logger.info(f"Initializing Faster-Whisper model: {self.config.model_name}")
        
        if self.config.use_cuda:
            try:
                self.logger.info("Attempting CUDA (FP16) initialization...")
                self.model = WhisperModel(
                    self.config.model_name,
                    device="cuda",
                    compute_type=self.config.cuda_compute_type
                )
                self.device_kind = "cuda"
                self.logger.info("✅ Running on CUDA (FP16)")
                return
            except Exception as e:
                self.logger.warning(f"CUDA initialization failed, falling back to CPU. Error: {str(e)}")
        
        self.logger.info("Initializing on CPU...")
        self.model = WhisperModel(
            self.config.model_name,
            device="cpu",
            compute_type=self.config.cpu_compute_type
        )
        self.device_kind = "cpu"
        self.logger.info("✅ Running on CPU (INT8)")

    def _transcribe(self, audio: np.ndarray) -> Tuple[Iterator[Segment], TranscriptionInfo]:
        """Run transcription with configured parameters."""
        if self.model is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        return self.model.transcribe(
            audio=audio,
            language=self.config.language,
            beam_size=self.config.beam_size,
            best_of=self.config.best_of,
            temperature=self.config.temperature,
            vad_filter=self.config.vad_filter,
            no_speech_threshold=self.config.no_speech_threshold
        )

    def process_audio(self, audio: np.ndarray, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio and return transcription with metrics."""
        ptt_up = metadata["ptt_up_ts"]
        ptt_down = metadata["ptt_down_ts"]
        capture_dur = metadata["capture_duration_s"]

        self.logger.info(
            f"Processing audio... | capture={capture_dur:.2f}s | "
            f"model={self.config.model_name} | device={self.device_kind}"
        )

        # Run transcription and measure time
        infer_start = time.perf_counter()
        segments, info = self._transcribe(audio)

        # Process segments and collect timing info
        first_seg_time = None
        texts: List[str] = []

        for seg in segments:
            if first_seg_time is None:
                first_seg_time = time.perf_counter()
            texts.append(seg.text)

        infer_end = time.perf_counter()
        text = " ".join(t.strip() for t in texts).strip()

        # Calculate latencies
        result = self._create_result(
            text=text,
            info=info,
            ptt_up=ptt_up,
            ptt_down=ptt_down,
            first_seg_time=first_seg_time,
            infer_end=infer_end
        )

        self._log_result(result)
        return result

    def _create_result(
        self, 
        text: str,
        info: TranscriptionInfo,
        ptt_up: float,
        ptt_down: float,
        first_seg_time: Optional[float],
        infer_end: float
    ) -> Dict[str, Any]:
        """Create result dictionary with metrics."""
        first_token_latency = (first_seg_time - ptt_up) if first_seg_time else (infer_end - ptt_up)
        
        return {
            "text": text,
            "metrics": {
                "first_token_latency_ms": first_token_latency * 1000,
                "total_latency_ms": (infer_end - ptt_up) * 1000,
                "press_to_final_ms": (infer_end - ptt_down) * 1000,
                "duration": info.duration,
                "language": info.language,
                "language_probability": info.language_probability
            }
        }

    def _log_result(self, result: Dict[str, Any]) -> None:
        """Log the transcription result and metrics."""
        metrics = result["metrics"]
        self.logger.info("Transcription complete")
        self.logger.info(f"Text: {result['text']!r}")
        self.logger.info(
            f"Metrics: first_token={metrics['first_token_latency_ms']:.0f}ms | "
            f"total={metrics['total_latency_ms']:.0f}ms | "
            f"press_to_final={metrics['press_to_final_ms']:.0f}ms"
        )
        self.logger.info(
            f"Info: duration={metrics['duration']:.2f}s | "
            f"language={metrics['language']} | "
            f"probability={metrics['language_probability']:.2f}"
        )
