"""
Telemetria a metriky pre monitorovanie výkonu.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import statistics
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Jeden bod merania metriky"""

    timestamp: datetime
    value: float
    metadata: Dict


@dataclass
class LatencyMetrics:
    """Metriky latencie pre rôzne časti spracovania"""

    transcription_ms: float
    first_token_ms: float
    assistant_ms: float
    total_ms: float
    metadata: Dict


class Telemetry:
    def __init__(self, metrics_file: Path):
        """
        Inicializuje systém telemetrie.

        Args:
            metrics_file: Cesta k súboru pre ukladanie metrík
        """
        self.metrics_file = metrics_file
        self.latencies: List[LatencyMetrics] = []
        self.transcription_quality: List[MetricPoint] = []
        self.assistant_quality: List[MetricPoint] = []

    def add_latency(self, metrics: LatencyMetrics):
        """Pridá nové meranie latencie"""
        self.latencies.append(metrics)
        self._save_metrics()

        # Analyzuj a loguj štatistiky
        if len(self.latencies) >= 10:
            self._analyze_latencies()

    def add_transcription_quality(
        self, confidence: float, metadata: Optional[Dict] = None
    ):
        """
        Pridá meranie kvality transkripcie

        Args:
            confidence: Skóre kvality (0-1)
            metadata: Voliteľné metadáta
        """
        self.transcription_quality.append(
            MetricPoint(
                timestamp=datetime.now(), value=confidence, metadata=metadata or {}
            )
        )

    def add_assistant_quality(
        self, response_length: int, metadata: Optional[Dict] = None
    ):
        """
        Pridá meranie kvality odpovede asistenta

        Args:
            response_length: Dĺžka odpovede
            metadata: Voliteľné metadáta
        """
        self.assistant_quality.append(
            MetricPoint(
                timestamp=datetime.now(),
                value=float(response_length),
                metadata=metadata or {},
            )
        )

    def _analyze_latencies(self):
        """Analyzuje nazbierané latencie a loguje štatistiky"""
        trans_times = [latency.transcription_ms for latency in self.latencies[-10:]]
        assist_times = [latency.assistant_ms for latency in self.latencies[-10:]]
        total_times = [latency.total_ms for latency in self.latencies[-10:]]

        logger.info("Štatistiky latencií (posledných 10):")
        logger.info(
            f"Transkripcia: {statistics.mean(trans_times):.0f}ms "
            f"(min={min(trans_times):.0f}, "
            f"max={max(trans_times):.0f})"
        )
        logger.info(
            f"Asistent: {statistics.mean(assist_times):.0f}ms "
            f"(min={min(assist_times):.0f}, "
            f"max={max(assist_times):.0f})"
        )
        logger.info(
            f"Celkovo: {statistics.mean(total_times):.0f}ms "
            f"(min={min(total_times):.0f}, "
            f"max={max(total_times):.0f})"
        )

    def _save_metrics(self):
        """Uloží metriky do súboru"""
        try:
            data = {
                "latencies": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "transcription_ms": latency.transcription_ms,
                        "first_token_ms": latency.first_token_ms,
                        "assistant_ms": latency.assistant_ms,
                        "total_ms": latency.total_ms,
                        "metadata": latency.metadata,
                    }
                    for latency in self.latencies[-100:]  # len posledných 100
                ],
                "transcription_quality": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "value": m.value,
                        "metadata": m.metadata,
                    }
                    for m in self.transcription_quality[-100:]
                ],
                "assistant_quality": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "value": m.value,
                        "metadata": m.metadata,
                    }
                    for m in self.assistant_quality[-100:]
                ],
            }

            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Chyba pri ukladaní metrík: {e}")


# Singleton inštancia
telemetry = Telemetry(Path("metrics.json"))
