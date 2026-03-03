"""NEO-TX configuration — Pydantic Settings with .env support."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # --- Alchemy connection (CPU-side, shadow desktop) ---
    alchemy_host: str = "http://localhost:8000"
    alchemy_token: str = ""

    # --- GPU Models (via Ollama) ---
    ollama_host: str = "http://localhost:11434"
    gpu_model: str = "qwen3:14b"              # 14B conversational (semantic, NOT coding)
    gpu_model_keep_alive: str = "30m"

    # --- Voice ---
    voice_enabled: bool = True
    wake_word: str = "hey_neo"
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    piper_model: str = "en_US-lessac-medium"
    voice_vad_aggressiveness: int = 2       # webrtcvad aggressiveness (0-3)
    voice_silence_ms: int = 800             # ms of silence to end recording
    voice_wake_threshold: float = 0.5       # openwakeword confidence threshold

    # --- TTS Engine ---
    tts_engine: str = "piper"               # "piper" or "fish"

    # --- Fish Speech (only when tts_engine=fish) ---
    fish_speech_port: int = 8080
    fish_speech_checkpoint: str = "checkpoints/openaudio-s1-mini"
    fish_speech_decoder_path: str = ""
    fish_speech_decoder_config: str = "modded_dac_vq"
    fish_speech_host: str = "127.0.0.1"
    fish_speech_startup_timeout: float = 60.0
    fish_speech_compile: bool = False
    fish_speech_sample_rate: int = 44100
    fish_speech_temperature: float = 0.8
    fish_speech_top_p: float = 0.8
    fish_speech_repetition_penalty: float = 1.1
    fish_speech_max_new_tokens: int = 1024
    fish_speech_reference_id: str = ""
    fish_speech_chunk_length: int = 200
    fish_speech_python_exe: str = ""              # Path to Fish Speech conda env python
    fish_speech_dir: str = ""                     # Fish Speech repo directory

    # --- GPU Mode ---
    gpu_mode: str = "single"                # "single" = VRAM swap, "dual" = all resident

    # --- System Tray ---
    tray_enabled: bool = True
    tray_novnc_url: str = "http://localhost:6080/vnc.html?autoconnect=true&resize=scale"

    # --- NEO-RX Knowledge (optional) ---
    neorx_host: str = "http://localhost:8110"
    knowledge_enabled: bool = True
    knowledge_max_docs: int = 3

    # --- NEO-TX Server ---
    host: str = "127.0.0.1"
    port: int = 8100
    log_level: str = "INFO"


settings = Settings()
