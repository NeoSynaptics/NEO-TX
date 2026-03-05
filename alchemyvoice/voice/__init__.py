"""Voice pipeline — Whisper STT + Piper/Fish Speech TTS + wake word detection.

Voice is the primary user interface for AlchemyVoice. Runs on GPU for fast response.
Mic → openWakeWord → Whisper STT → 14B interprets → routes (answer directly
or send task to Alchemy for shadow desktop work) → TTS → speaker.

Imports are lazy to avoid crashing when voice deps aren't installed or
are incompatible (e.g., webrtcvad on Python 3.13).
"""


def __getattr__(name: str):
    """Lazy import voice components on first access."""
    _exports = {
        "AudioStream": "alchemyvoice.voice.audio",
        "SpeechListener": "alchemyvoice.voice.listener",
        "PipelineState": "alchemyvoice.voice.pipeline",
        "VoicePipeline": "alchemyvoice.voice.pipeline",
        "WhisperSTT": "alchemyvoice.voice.stt",
        "PiperTTS": "alchemyvoice.voice.tts",
        "FishSpeechTTS": "alchemyvoice.voice.tts",
        "FishSpeechProcess": "alchemyvoice.voice.fish_speech",
        "VRAMManager": "alchemyvoice.voice.vram_manager",
        "GPUMode": "alchemyvoice.voice.vram_manager",
        "WakeWordDetector": "alchemyvoice.voice.wake_word",
    }
    if name in _exports:
        import importlib

        module = importlib.import_module(_exports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'alchemyvoice.voice' has no attribute {name!r}")


__all__ = [
    "AudioStream",
    "SpeechListener",
    "PipelineState",
    "VoicePipeline",
    "WhisperSTT",
    "PiperTTS",
    "FishSpeechTTS",
    "FishSpeechProcess",
    "VRAMManager",
    "GPUMode",
    "WakeWordDetector",
]
