"""
Elena STT (PTT: F12) – Faster-Whisper (medium, SK)
Speech-to-Text s Push-to-Talk funkciou, využívajúci Faster-Whisper model a OpenAI Assistant API.
"""

import sys
import yaml
import queue
import threading
from pathlib import Path
from typing import Dict, Any
from pynput import keyboard
import time
from datetime import datetime
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Initialize colorama for Windows color support
init()
from collections import deque
import numpy as np
from math import ceil
from scipy.signal import resample_poly
import sounddevice as sd

from utils.logging_config import setup_logging
from audio.processor import AudioProcessor, AudioConfig
from stt.processor import STTProcessor, WhisperConfig
from assistant.processor import AssistantProcessor, AssistantConfig

# Load environment variables
load_dotenv()

# Setup logging first thing
logger = setup_logging()
print(f"\n{Fore.CYAN}Elena STT{Style.RESET_ALL} - Speech-to-Text s Push-to-Talk (F12)\n")

# Načítanie konfigurácie
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        print(f"{Fore.GREEN}Načítavam konfiguráciu...{Style.RESET_ALL}")
        config = yaml.safe_load(f)
except Exception as e:
    print(f"{Fore.RED}❌ Chyba pri načítaní konfigurácie: {e}{Style.RESET_ALL}")
    sys.exit(1)

# Load settings from config
MODEL_SIZE = config["model"]["size"]
LANGUAGE = config["model"]["language"]
USE_CUDA_FIRST = config["model"]["cuda"]["enabled"]
COMPUTE_TYPE_CUDA = config["model"]["cuda"]["compute_type"]
COMPUTE_TYPE_CPU = config["model"]["cpu"]["compute_type"]

# Validate model size
VALID_MODELS = ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]
if MODEL_SIZE not in VALID_MODELS:
    print(f"{Fore.RED}❌ Neplatná veľkosť modelu: {MODEL_SIZE}")
    print(f"   Povolené hodnoty: {', '.join(VALID_MODELS)}{Style.RESET_ALL}")
    sys.exit(1)

# Audio settings
INPUT_SAMPLE_RATE = config["audio"]["sample_rate"]
CHANNELS = config["audio"]["channels"]
BLOCKSIZE = config["audio"]["blocksize"]
PRE_ROLL_SEC = config["audio"]["pre_roll_sec"]
POST_ROLL_SEC = config["audio"]["post_roll_sec"]
INPUT_DEVICE_INDEX = config["audio"]["input_device_index"]

# STT parameters
BEAM_SIZE = config["model"]["inference"]["beam_size"]
BEST_OF = config["model"]["inference"]["best_of"]
TEMPERATURE = config["model"]["inference"]["temperature"]
VAD_FILTER = config["model"]["inference"]["vad_filter"]
NO_SPEECH_THRESHOLD = config["model"]["inference"]["no_speech_threshold"]

# Controls
PTT_KEY = getattr(keyboard.Key, config["controls"]["ptt_key"])
PRINT_PARTIALS = config["controls"]["print_partials"]

# -------------------------
# Načítanie modelu
# -------------------------
print(f"\n{Fore.GREEN}Načítavam Faster-Whisper model: {MODEL_SIZE}{Style.RESET_ALL}")
from faster_whisper import WhisperModel
import os

# Pridaj CUDA cestu do PATH
cuda_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"
if cuda_path not in os.environ["PATH"]:
    os.environ["PATH"] = cuda_path + os.pathsep + os.environ["PATH"]

def _load_model():
    if USE_CUDA_FIRST:
        try:
            print(f"{Fore.YELLOW}Kontrolujem CUDA...{Style.RESET_ALL}")
            import torch
            if not torch.cuda.is_available():
                print(f"{Fore.RED}CUDA nie je dostupná - chýba CUDA toolkit alebo ovládače{Style.RESET_ALL}")
                raise RuntimeError("CUDA is not available")
            
            cuda_device = torch.cuda.get_device_properties(0)
            print(f"{Fore.YELLOW}GPU: {cuda_device.name}{Style.RESET_ALL}")
            
            print(f"{Fore.YELLOW}Inicializujem Whisper na CUDA (FP16)...{Style.RESET_ALL}")
            m = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE_CUDA)
            print(f"{Fore.GREEN}Model beží na CUDA (FP16){Style.RESET_ALL}")
            return m, "cuda"
        except Exception as e:
            print(f"{Fore.RED}❌ CUDA zlyhala: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚠️ Prepínam na CPU{Style.RESET_ALL}")
    print(f"{Fore.BLUE}💻 CPU režim (INT8)...{Style.RESET_ALL}")
    m = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE_CPU)
    print(f"{Fore.GREEN}✅ Beží na CPU (INT8){Style.RESET_ALL}")
    return m, "cpu"

model, device_kind = _load_model()

# -------------------------
# Assistant inicializácia
# -------------------------
try:
    assistant_config = AssistantConfig()
    assistant = AssistantProcessor(assistant_config)
    print(f"{Fore.GREEN}OpenAI Asistent API pripravené{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}Chyba pri inicializácii OpenAI Asistenta: {e}{Style.RESET_ALL}")
    sys.exit(1)

# -------------------------
# Stav a fronty
# -------------------------
MODEL_SAMPLE_RATE = 16000  # očakávanie modelu
block_duration = BLOCKSIZE / float(INPUT_SAMPLE_RATE)
pre_blocks = max(1, ceil(PRE_ROLL_SEC / block_duration))
post_blocks = max(1, ceil(POST_ROLL_SEC / block_duration))

pre_buffer = deque(maxlen=pre_blocks)      # uchová posledné bloky pred PTT
capture_state = "idle"                     # "idle" | "recording" | "postroll"
current_frames = []                        # zoznam 1D numpy blokov
post_blocks_left = 0

ptt_down_ts = None
ptt_up_ts = None

jobs = queue.Queue()   # fronta na STT úlohy (audio, metadata)

lock = threading.Lock()

# -------------------------
# Audio callback
# -------------------------
def audio_callback(indata, frames, time_info, status):
    global capture_state, post_blocks_left
    # indata shape: (frames, channels); berieme mono
    mono = indata[:, 0].copy()

    with lock:
        # kruhový buffer na pre-roll
        pre_buffer.append(mono)

        if capture_state == "recording":
            current_frames.append(mono)

        elif capture_state == "postroll":
            current_frames.append(mono)
            post_blocks_left -= 1
            if post_blocks_left <= 0:
                # uzavri záznam a odošli do fronty
                _finalize_capture_locked()

def _finalize_capture_locked():
    global capture_state, current_frames, ptt_down_ts, ptt_up_ts
    if not current_frames:
        # nič nenahraté (mohlo sa stať pri omyle)
        capture_state = "idle"
        return

    audio = np.concatenate(current_frames, axis=0)
    duration_s = len(audio) / float(INPUT_SAMPLE_RATE)

    # resample ak treba → 16 kHz pre model
    if INPUT_SAMPLE_RATE != MODEL_SAMPLE_RATE:
        audio = resample_poly(audio, MODEL_SAMPLE_RATE, INPUT_SAMPLE_RATE)
        rec_sr = INPUT_SAMPLE_RATE
        final_sr = MODEL_SAMPLE_RATE
    else:
        rec_sr = INPUT_SAMPLE_RATE
        final_sr = INPUT_SAMPLE_RATE

    # priprav job do worker vlákna
    meta = {
        "ptt_down_ts": ptt_down_ts,
        "ptt_up_ts": ptt_up_ts,
        "capture_duration_s": duration_s,
        "record_sr": rec_sr,
        "final_sr": final_sr,
        "device_kind": device_kind,
    }
    jobs.put((audio.astype(np.float32), meta))

    # reset
    current_frames = []
    capture_state = "idle"

# -------------------------
# PTT (klávesnica)
# -------------------------
def on_press(key):
    global capture_state, current_frames, post_blocks_left, ptt_down_ts
    if key == PTT_KEY:
        with lock:
            if capture_state == "idle":
                # začíname nahrávať – skopíruj pre-roll
                current_frames = [blk.copy() for blk in pre_buffer]
                capture_state = "recording"
                ptt_down_ts = time.perf_counter()
                print(f"\n{Fore.CYAN}Nahrávam... ({datetime.now().strftime('%H:%M:%S')}){Style.RESET_ALL}")

def on_release(key):
    global capture_state, post_blocks_left, ptt_up_ts
    if key == PTT_KEY:
        with lock:
            if capture_state == "recording":
                # prechod do post-roll zberu
                capture_state = "postroll"
                post_blocks_left = post_blocks
                ptt_up_ts = time.perf_counter()
                print(f"{Fore.YELLOW}Spracovávam... ({datetime.now().strftime('%H:%M:%S')}){Style.RESET_ALL}")

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.daemon = True
listener.start()

# -------------------------
# STT worker
# -------------------------
def stt_worker():
    while True:
        audio, meta = jobs.get()
        if audio is None:
            break
        process_stt(audio, meta)
        jobs.task_done()

def process_stt(audio, meta):
    # Latencie
    ptt_up = meta["ptt_up_ts"]
    ptt_down = meta["ptt_down_ts"]
    capture_dur = meta["capture_duration_s"]

    # Spustíme transkripciu
    infer_start = time.perf_counter()
    segments, info = model.transcribe(
        audio=audio,
        language=LANGUAGE,
        beam_size=BEAM_SIZE,
        best_of=BEST_OF,
        temperature=TEMPERATURE,
        vad_filter=VAD_FILTER,
        no_speech_threshold=NO_SPEECH_THRESHOLD,
    )

    first_seg_time = None
    texts = []

    for i, seg in enumerate(segments):
        if first_seg_time is None:
            first_seg_time = time.perf_counter()
        if PRINT_PARTIALS:
            print(f"{Fore.CYAN}  ↪ {seg.text}{Style.RESET_ALL}")
        texts.append(seg.text)

    infer_end = time.perf_counter()
    text = " ".join(t.strip() for t in texts).strip()

    # Výpočty latencií
    first_token_latency = (first_seg_time - ptt_up) if first_seg_time else (infer_end - ptt_up)
    total_latency = infer_end - ptt_up
    press_to_final = infer_end - ptt_down

    # Výpis
    if text:
        print(f"{Fore.GREEN}Text: {Style.BRIGHT}{text}{Style.RESET_ALL}")
        
        # Získanie odpovede od asistenta
        try:
            print(f"{Fore.YELLOW}Generujem odpoveď od Eleny...{Style.RESET_ALL}")
            assistant_start = time.perf_counter()
            assistant_response = assistant.get_response("Používateľ", text)
            assistant_end = time.perf_counter()
            if assistant_response:
                print(f"{Fore.MAGENTA}Elena: {Style.BRIGHT}{assistant_response}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Elena nemohla vygenerovať odpoveď{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Chyba pri komunikácii s OpenAI: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Nezachytený žiadny text{Style.RESET_ALL}")
    
    # Štatistiky v jemnejšej farbe
    # Štatistiky
    print(f"\n{Fore.BLUE}Štatistiky:{Style.RESET_ALL}")
    print(f"  Nahrávka: {capture_dur:.1f}s")
    print(f"  Prepis: {total_latency:.1f}s")
    if 'assistant_start' in locals() and 'assistant_end' in locals():
        assistant_latency = assistant_end - ptt_up
        print(f"  Celkový čas: {assistant_latency:.1f}s")
    
    # Detailnejšie časy
    if first_token_latency < 1.0:
        token_color = Fore.GREEN
    elif first_token_latency < 2.0:
        token_color = Fore.YELLOW
    else:
        token_color = Fore.RED
    
    # Časy a jazyk
    print(f"{Fore.CYAN}Detekcia:{Style.RESET_ALL}")
    print(f"  Prvé slová: {token_color}{first_token_latency*1000:.0f}ms{Style.RESET_ALL}")
    if 'assistant_start' in locals() and 'assistant_end' in locals():
        assistant_gen_time = assistant_end - assistant_start
        color = Fore.GREEN if assistant_gen_time < 2.0 else (Fore.YELLOW if assistant_gen_time < 4.0 else Fore.RED)
        print(f"  Odpoveď Eleny: {color}{assistant_gen_time*1000:.0f}ms{Style.RESET_ALL}")
    
    if info.language_probability > 0.9:
        print(f"  Jazyk: {Fore.GREEN}{info.language}{Style.RESET_ALL}")
    else:
        print(f"  Jazyk: {Fore.YELLOW}{info.language} ({info.language_probability:.0%}){Style.RESET_ALL}")

worker_thread = threading.Thread(target=stt_worker, daemon=True)
worker_thread.start()

# -------------------------
# Audio stream
# -------------------------
print(f"\n{Fore.CYAN}Audio nastavenia:{Style.RESET_ALL}")
print(f"  Vzorkovanie: {INPUT_SAMPLE_RATE} Hz")
print(f"  Pre-roll: {PRE_ROLL_SEC*1000:.0f} ms")
print(f"  Post-roll: {POST_ROLL_SEC*1000:.0f} ms")

print(f"\n{Fore.GREEN}Systém je pripravený{Style.RESET_ALL}")
print(f"{Fore.CYAN}Stlač a drž {Style.BRIGHT}F12{Style.NORMAL} pre nahrávanie, pusti pre prepis.{Style.RESET_ALL}")
print(f"{Fore.CYAN}Pre ukončenie stlač Ctrl+C{Style.RESET_ALL}\n")

try:
    with sd.InputStream(
        samplerate=INPUT_SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=BLOCKSIZE,
        device=INPUT_DEVICE_INDEX,
        callback=audio_callback,
    ):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}Ukončujem program...{Style.RESET_ALL}")
except Exception as e:
    print(f"\n{Fore.RED}Chyba: {e}{Style.RESET_ALL}")
finally:
    jobs.put((None, None))
