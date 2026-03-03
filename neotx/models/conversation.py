"""Conversation manager — context window and history for 14B chat."""

from __future__ import annotations

import logging
from collections import defaultdict
from uuid import UUID

from neotx.models.schemas import ChatMessage

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are Neo, a local AI assistant. You talk like a sharp, knowledgeable friend — "
    "not a textbook. The user is speaking to you by VOICE, so your responses will be "
    "read aloud.\n\n"
    "Rules:\n"
    "- Keep responses SHORT: 2-4 sentences max unless asked for detail.\n"
    "- Be direct and opinionated. Say what YOU think, don't list every angle.\n"
    "- Sound natural — like talking, not writing an essay.\n"
    "- No bullet points, no numbered lists, no markdown. Just speak.\n"
    "- If the user asks about something complex, give the interesting hook first, "
    "then offer to go deeper.\n"
    "- For GUI tasks (clicking, browsing, desktop apps), delegate to a background vision agent.\n"
    "- Never say 'As an AI' or 'I don't have feelings'. Just be real."
)


class ConversationManager:
    """Manages conversation history and context windows.

    In-memory storage keyed by conversation_id. Uses a sliding window
    to stay within the 14B's context limit.
    """

    def __init__(
        self,
        max_history: int = 50,
        max_tokens_estimate: int = 24000,
        system_prompt: str | None = None,
    ) -> None:
        self._conversations: dict[UUID, list[ChatMessage]] = defaultdict(list)
        self._max_history = max_history
        self._max_tokens = max_tokens_estimate
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def get_messages(
        self,
        conversation_id: UUID,
        knowledge_context: list[str] | None = None,
    ) -> list[ChatMessage]:
        """Get full message list for Ollama including system prompt.

        Args:
            conversation_id: The conversation to fetch messages for.
            knowledge_context: Optional list of distilled knowledge docs
                to inject into the system prompt (from NEO-RX Nightwatch).

        Returns [system, ...history] trimmed to fit context window.
        """
        history = self._conversations[conversation_id]

        if len(history) > self._max_history:
            history = history[-self._max_history :]
            self._conversations[conversation_id] = history

        # Build system prompt with optional knowledge injection
        prompt = self._system_prompt
        if knowledge_context:
            knowledge_block = "\n\n---\nRelevant knowledge:\n" + "\n\n".join(
                knowledge_context
            )
            prompt += knowledge_block

        system_msg = ChatMessage(role="system", content=prompt)
        messages = [system_msg] + list(history)

        # Estimate tokens (~4 chars per token) and trim oldest if over budget
        total_chars = sum(len(m.content) for m in messages)
        while total_chars > self._max_tokens * 4 and len(messages) > 2:
            removed = messages.pop(1)
            total_chars -= len(removed.content)

        return messages

    def add_user_message(self, conversation_id: UUID, content: str) -> ChatMessage:
        msg = ChatMessage(role="user", content=content)
        self._conversations[conversation_id].append(msg)
        return msg

    def add_assistant_message(self, conversation_id: UUID, content: str) -> ChatMessage:
        msg = ChatMessage(role="assistant", content=content)
        self._conversations[conversation_id].append(msg)
        return msg

    def clear(self, conversation_id: UUID) -> None:
        self._conversations.pop(conversation_id, None)

    def active_conversations(self) -> int:
        return len(self._conversations)
