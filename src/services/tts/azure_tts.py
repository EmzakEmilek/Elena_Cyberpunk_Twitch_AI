"""
Azure Cognitive Services TTS implementácia.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)


@dataclass
class TTSWordBoundary:
    """Reprezentuje boundary event pre jedno slovo."""
    time_ms: int  # Čas v milisekundách
    text_offset: int  # Offset v texte
    word_length: int  # Dĺžka slova


class TTSError(Exception):
    """Základná výnimka pre TTS chyby."""
    pass


class TTSConfigError(TTSError):
    """Výnimka pre chyby v konfigurácii."""
    pass


class TTSServiceError(TTSError):
    """Výnimka pre chyby Azure služby."""
    pass


class AzureTTS:
    """Azure Cognitive Services TTS implementácia."""

    def __init__(self, voice: Optional[str] = None):
        """
        Inicializuje Azure TTS.
        
        Args:
            voice: Voliteľný hlas na použitie. Ak None, použije sa hodnota z env.
        """
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.service_region = os.getenv("AZURE_SPEECH_REGION")
        self.voice_name = voice or os.getenv("AZURE_SPEECH_VOICE", "sk-SK-ViktoriaNeural")

        if not self.speech_key or not self.service_region:
            raise TTSConfigError(
                "Chýbajú Azure credentials. Skontrolujte AZURE_SPEECH_KEY a "
                "AZURE_SPEECH_REGION v .env súbore."
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.service_region
        )
        self.speech_config.speech_synthesis_voice_name = self.voice_name
        
        # Nastavenie výstupného formátu
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm
        )

        logger.info(
            f"AzureTTS inicializované (voice={self.voice_name}, region={self.service_region})"
        )

    async def speak_async(self, text: str, on_word_boundary=None, on_completed=None) -> List[TTSWordBoundary]:
        """
        Asynchrónne prehrá text a vráti word boundaries.
        
        Args:
            text: Text na prehranie
            on_word_boundary: Voliteľný callback pre word boundary eventy
            on_completed: Voliteľný callback po dokončení syntézy
            
        Returns:
            List of word boundary events
        """
        boundaries: List[TTSWordBoundary] = []
        # Použitie default audio výstupu
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, 
            audio_config=audio_config
        )

        # Event handler pre word boundary eventy
        def handle_boundary_event(evt: speechsdk.SpeechSynthesisWordBoundaryEventArgs):
            # Konverzia zo 100-nanosekúnd na milisekundy
            time_ms = evt.audio_offset // 10000
            boundary = TTSWordBoundary(
                time_ms=time_ms,
                text_offset=evt.text_offset,
                word_length=evt.word_length
            )
            boundaries.append(boundary)
            
            # Ak je nastavený callback, zavoláme ho
            if on_word_boundary:
                loop = asyncio.get_event_loop()
                loop.create_task(on_word_boundary(text, boundary))

        done_event = asyncio.Event()
        error = None

        def handle_canceled(evt: speechsdk.SpeechSynthesisEventArgs):
            nonlocal error
            details = speechsdk.CancellationDetails.from_result(evt.result)
            error = TTSServiceError(
                f"Syntéza zlyhala: {details.reason} - {details.error_details}"
            )
            done_event.set()

        def handle_completed(evt: speechsdk.SpeechSynthesisEventArgs):
            logger.info("Syntéza dokončená, prehrávanie ukončené")
            if on_completed:
                on_completed(evt)
            done_event.set()

        # Pripojenie event handlerov
        synthesizer.synthesis_word_boundary.connect(handle_boundary_event)
        synthesizer.synthesis_completed.connect(handle_completed)
        synthesizer.synthesis_canceled.connect(handle_canceled)

        # Spustenie syntézy
        result = synthesizer.speak_text_async(text)
        
        try:
            # Čakáme na dokončenie syntézy
            await asyncio.wait_for(done_event.wait(), timeout=30.0)
            
            if error:
                raise error
                
            if not result:
                raise TTSServiceError("Syntéza zlyhala bez špecifickej chyby")
                
        except asyncio.TimeoutError:
            logger.error("Timeout pri čakaní na TTS syntézu")
            raise TTSServiceError("TTS syntéza trvala príliš dlho")
        except Exception as e:
            logger.error(f"Chyba pri TTS syntéze: {str(e)}")
            raise

        return sorted(boundaries, key=lambda x: x.time_ms)

    def speak(self, text: str) -> List[TTSWordBoundary]:
        """
        Synchrónna verzia speak metódy.
        
        Args:
            text: Text na prehranie
            
        Returns:
            List of word boundary events
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.speak_async(text))

    async def synthesize_to_wav(
        self, 
        text: str, 
        path: Path
    ) -> List[TTSWordBoundary]:
        """
        Syntetizuje text do WAV súboru.
        
        Args:
            text: Text na syntézu
            path: Cesta k výstupnému WAV súboru
            
        Returns:
            List of word boundary events
        """
        boundaries: List[TTSWordBoundary] = []
        audio_config = speechsdk.AudioConfig(filename=str(path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, 
            audio_config=audio_config
        )

        def handle_boundary_event(evt: speechsdk.SpeechSynthesisWordBoundaryEventArgs):
            time_ms = evt.audio_offset // 10000
            boundaries.append(TTSWordBoundary(
                time_ms=time_ms,
                text_offset=evt.text_offset,
                word_length=evt.word_length
            ))

        synthesizer.synthesis_word_boundary.connect(handle_boundary_event)

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def handle_result(evt: speechsdk.SpeechSynthesisEventArgs):
            if evt.result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                future.set_result(True)
            else:
                details = speechsdk.CancellationDetails.from_result(evt.result)
                future.set_exception(TTSServiceError(
                    f"Syntéza do WAV zlyhala: {details.reason} - {details.error_details}"
                ))

        synthesizer.synthesis_completed.connect(handle_result)
        synthesizer.synthesis_canceled.connect(handle_result)

        synthesizer.speak_text_async(text)

        try:
            await future
        except Exception as e:
            logger.error(f"Chyba pri syntéze do WAV: {str(e)}")
            raise

        return sorted(boundaries, key=lambda x: x.time_ms)
