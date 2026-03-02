"""NEO-TX configuration — Pydantic Settings with .env support."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # --- AlchemyGoldOS connection ---
    alchemy_host: str = "http://localhost:8000"
    alchemy_token: str = ""

    # --- Shadow Desktop (WSL2) ---
    wsl_distro: str = "Ubuntu"
    display_num: int = 99
    vnc_port: int = 5900
    novnc_port: int = 6080
    resolution: str = "1920x1080x24"

    # --- Agent ---
    agent_max_steps: int = 50
    agent_screenshot_interval: float = 1.0
    agent_timeout: float = 300.0

    # --- Claude Computer Use (Phase 2) ---
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5-20250929"

    # --- Voice (Phase 4) ---
    wake_word: str = "hey_neo"
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    piper_model: str = "en_US-lessac-medium"

    # --- Task Router ---
    default_route: str = "shadow"  # "shadow" or "api_direct"

    # --- NEO-TX Server ---
    host: str = "127.0.0.1"
    port: int = 8100


settings = Settings()
