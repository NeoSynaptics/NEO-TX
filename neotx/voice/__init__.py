"""Voice pipeline — Whisper STT + Piper TTS + wake word detection.

Voice is the primary user interface for NEO-TX. Runs on GPU for fast response.
Mic → openWakeWord → Whisper STT → 14B interprets → routes (answer directly
or send task to Alchemy for shadow desktop work) → Piper TTS → speaker.

Imports are lazy to avoid crashing when voice deps aren't installed or
are incompatible (e.g., webrtcvad on Python 3.13).
"""


def __getattr__(name: str):
    """Lazy import voice components on first access."""
    _exports = {
        "AudioStream": "neotx.voice.audio",
        "SpeechListener": "neotx.voice.listener",
        "PipelineState": "neotx.voice.pipeline",
        "VoicePipeline": "neotx.voice.pipeline",
        "WhisperSTT": "neotx.voice.stt",
        "PiperTTS": "neotx.voice.tts",
        "WakeWordDetector": "neotx.voice.wake_word",
    }
    if name in _exports:
        import importlib

        module = importlib.import_module(_exports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'neotx.voice' has no attribute {name!r}")


__all__ = [
    "AudioStream",
    "SpeechListener",
    "PipelineState",
    "VoicePipeline",
    "WhisperSTT",
    "PiperTTS",
    "WakeWordDetector",
]
