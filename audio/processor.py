import numpy as np
import sounddevice as sd
import threading
import time
import logging
from datetime import datetime
from collections import deque
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
from math import ceil
from scipy.signal import resample_poly

@dataclass
class AudioConfig:
    sample_rate: int
    channels: int
    blocksize: int
    pre_roll_sec: float
    post_roll_sec: float
    input_device_index: Optional[int]

class AudioProcessor:
    def __init__(self, config: AudioConfig, on_capture_complete: Callable):
        """Initialize audio processor with configuration."""
        self.config = config
        self.on_capture_complete = on_capture_complete
        self.logger = logging.getLogger("elena_stt")

        # Calculate buffer sizes
        self.block_duration = config.blocksize / float(config.sample_rate)
        self.pre_blocks = max(1, ceil(config.pre_roll_sec / self.block_duration))
        self.post_blocks = max(1, ceil(config.post_roll_sec / self.block_duration))

        # State
        self.pre_buffer = deque(maxlen=self.pre_blocks)
        self.capture_state = "idle"  # "idle" | "recording" | "postroll"
        self.current_frames: List[np.ndarray] = []
        self.post_blocks_left = 0
        self.ptt_down_ts = None
        self.ptt_up_ts = None

    def audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Handle incoming audio data."""
        try:
            mono = indata[:, 0].copy()
            
            with threading.Lock():
                self.pre_buffer.append(mono)

                if self.capture_state == "recording":
                    self.current_frames.append(mono)
                elif self.capture_state == "postroll":
                    self.current_frames.append(mono)
                    self.post_blocks_left -= 1
                    if self.post_blocks_left <= 0:
                        self._finalize_capture()
        except Exception as e:
            self.logger.error(f"Error in audio callback: {str(e)}", exc_info=True)

    def start_recording(self):
        """Start recording with pre-roll buffer."""
        with threading.Lock():
            if self.capture_state == "idle":
                self.current_frames = [blk.copy() for blk in self.pre_buffer]
                self.capture_state = "recording"
                self.ptt_down_ts = time.perf_counter()
                self.logger.info(f"Recording started at {datetime.now().strftime('%H:%M:%S')}")

    def stop_recording(self):
        """Stop recording and start post-roll collection."""
        with threading.Lock():
            if self.capture_state == "recording":
                self.capture_state = "postroll"
                self.post_blocks_left = self.post_blocks
                self.ptt_up_ts = time.perf_counter()
                self.logger.info(f"Recording stopped at {datetime.now().strftime('%H:%M:%S')}")

    def _finalize_capture(self):
        """Process and finalize the captured audio."""
        if not self.current_frames:
            self.capture_state = "idle"
            return

        try:
            audio = np.concatenate(self.current_frames, axis=0)
            duration_s = len(audio) / float(self.config.sample_rate)

            metadata = {
                "ptt_down_ts": self.ptt_down_ts,
                "ptt_up_ts": self.ptt_up_ts,
                "capture_duration_s": duration_s,
                "sample_rate": self.config.sample_rate
            }

            self.on_capture_complete(audio.astype(np.float32), metadata)
            
            self.current_frames = []
            self.capture_state = "idle"
        except Exception as e:
            self.logger.error(f"Error finalizing capture: {str(e)}", exc_info=True)
            self.capture_state = "idle"

    def start_stream(self):
        """Start the audio input stream."""
        try:
            return sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype="float32",
                blocksize=self.config.blocksize,
                device=self.config.input_device_index,
                callback=self.audio_callback
            )
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {str(e)}", exc_info=True)
            raise
