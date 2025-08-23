# Elena - Cyberpunk Twitch AI

Real-time Speech-to-Text systém pre Twitch streamovanie s push-to-talk funkciou, postavený na Faster-Whisper.

## Vlastnosti

- 🎤 Push-to-Talk (F12) pre pohodlné ovládanie
- ⚡ GPU akcelerácia cez CUDA
- 🔊 Detekcia ticha (VAD)
- 🎯 Optimalizovaná latencia
- 🎨 Farebný výstup v termináli
- ⚙️ Konfigurovateľné cez YAML

## Požiadavky

- Python 3.11+
- NVIDIA GPU s CUDA 11.8
- cuDNN v8.9.7
- PyTorch s CUDA podporou

## Inštalácia

1. Vytvorte virtuálne prostredie:
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. Nainštalujte závislosti:
```bash
pip install -r requirements.txt
```

3. Nakonfigurujte `config.yaml` podľa potreby

## Použitie

1. Aktivujte virtuálne prostredie:
```bash
.\.venv\Scripts\activate
```

2. Spustite program:
```bash
python elena_stt_ptt.py
```

3. Držte F12 pre nahrávanie, pustite pre prepis na text

## Konfigurácia

V `config.yaml` môžete nastaviť:
- Veľkosť modelu (base, medium, large-v2, large-v3)
- Jazyk (predvolene slovenčina)
- Audio parametre
- Push-to-talk klávesu
- CUDA/CPU preferencie
