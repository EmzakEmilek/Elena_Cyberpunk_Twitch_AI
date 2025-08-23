"""
Text-to-Speech služby pre Elenu.
"""

from .azure_tts import AzureTTS, TTSError, TTSConfigError, TTSServiceError

__all__ = ['AzureTTS', 'TTSError', 'TTSConfigError', 'TTSServiceError']
