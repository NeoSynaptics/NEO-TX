"""Smart router — intent classification + model routing."""

from neotx.router.cascade import CascadeStrategy, ConversationToVisionCascade
from neotx.router.classifier import classify_from_keywords, parse_intent_tag
from neotx.router.router import SmartRouter

__all__ = [
    "SmartRouter",
    "classify_from_keywords",
    "parse_intent_tag",
    "CascadeStrategy",
    "ConversationToVisionCascade",
]
