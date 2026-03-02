"""Voice pipeline — Whisper STT + Piper TTS + wake word detection.

Voice is the primary user interface for NEO-TX. Runs on GPU for fast response.
Mic → openWakeWord → Whisper STT → 14B interprets → routes (answer directly
or send task to Alchemy for shadow desktop work) → Piper TTS → speaker.
"""
