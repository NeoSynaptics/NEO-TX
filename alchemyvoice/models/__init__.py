"""GPU model management — registry, providers, conversation context.

AlchemyVoice owns the GPU models for fast user interaction:
- 14B conversational model (semantic understanding, NOT coding)
- Small specialized models (~2B) for specific fast tasks
"""

from alchemyvoice.models.conversation import ConversationManager
from alchemyvoice.models.provider import AlchemyProvider, ModelProvider, OllamaProvider
from alchemyvoice.models.registry import ModelRegistry, build_default_registry
from alchemyvoice.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelCard,
    ModelLocation,
    RouteDecision,
    RouteIntent,
    SpeedTier,
    StreamChunk,
)

__all__ = [
    "ConversationManager",
    "AlchemyProvider",
    "ModelProvider",
    "OllamaProvider",
    "ModelRegistry",
    "build_default_registry",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ModelCapability",
    "ModelCard",
    "ModelLocation",
    "RouteDecision",
    "RouteIntent",
    "SpeedTier",
    "StreamChunk",
]
