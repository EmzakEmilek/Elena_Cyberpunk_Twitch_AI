"""
Modul pre spracovanie klávesových skratiek.
"""

from typing import Callable
from pynput import keyboard
import logging

logger = logging.getLogger(__name__)


class KeyboardListener:
    """
    Trieda pre zapuzdrenie logiky pynput listenera.
    """

    def __init__(
        self, ptt_key: str, on_press_callback: Callable, on_release_callback: Callable
    ):
        """
        Inicializuje listener.

        Args:
            ptt_key: Klávesa, ktorá spúšťa nahrávanie (napr. "f12").
            on_press_callback: Funkcia, ktorá sa zavolá pri stlačení klávesy.
            on_release_callback: Funkcia, ktorá sa zavolá pri uvoľnení klávesy.
        """
        self.ptt_key_str = ptt_key
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback
        self.listener: keyboard.Listener = None

        try:
            self.ptt_key = getattr(keyboard.Key, ptt_key)
        except AttributeError:
            logger.warning(
                f"Neznáma klávesa '{ptt_key}' v konfigurácii. Používam F12 ako predvolenú."
            )
            self.ptt_key = keyboard.Key.f12

    def _on_press(self, key):
        if key == self.ptt_key:
            self.on_press_callback()

    def _on_release(self, key):
        if key == self.ptt_key:
            self.on_release_callback()

    def start(self):
        """Spustí listener v samostatnom threade."""
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            logger.info(
                f"Keyboard listener spustený. PTT klávesa: {self.ptt_key_str.upper()}"
            )

    def stop(self):
        """Zastaví listener."""
        if self.listener and self.listener.is_alive():
            self.listener.stop()
            logger.info("Keyboard listener zastavený.")
