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

    # --- System Tray ---
    tray_enabled: bool = True
    tray_novnc_url: str = "http://localhost:6080/vnc.html?autoconnect=true&resize=scale"

    # --- NEO-TX Server ---
    host: str = "127.0.0.1"
    port: int = 8100
    log_level: str = "INFO"


settings = Settings()
