"""Typed HTTP client for NEO-TX → Alchemy API calls.

NEO-TX uses this to delegate GUI tasks, control the shadow desktop,
check model status, and relay approval decisions.
"""

from __future__ import annotations

from uuid import UUID

import httpx

from neotx.schemas import (
    ApprovalDecision,
    ApprovalDecisionResponse,
    ModelsResponse,
    ShadowHealthResponse,
    ShadowStartRequest,
    ShadowStartResponse,
    ShadowStopResponse,
    TaskStatusResponse,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    VisionTaskRequest,
    VisionTaskResponse,
)


class AlchemyClient:
    """Async HTTP client for calling Alchemy endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- Vision (GUI tasks) ---

    async def submit_task(
        self,
        goal: str,
        callback_url: str = "http://localhost:8100",
        context: dict | None = None,
    ) -> VisionTaskResponse:
        """Submit a GUI task for Alchemy's vision agent."""
        req = VisionTaskRequest(goal=goal, callback_url=callback_url, context=context)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/vision/task",
                json=req.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return VisionTaskResponse.model_validate(resp.json())

    async def analyze(
        self,
        screenshot_b64: str,
        goal: str,
        context: dict | None = None,
    ) -> VisionAnalyzeResponse:
        """Send a screenshot for single-step analysis."""
        req = VisionAnalyzeRequest(
            screenshot_b64=screenshot_b64, goal=goal, context=context
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/vision/analyze",
                json=req.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return VisionAnalyzeResponse.model_validate(resp.json())

    async def task_status(self, task_id: UUID) -> TaskStatusResponse:
        """Poll the current status of a vision task."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/vision/task/{task_id}/status")
            resp.raise_for_status()
            return TaskStatusResponse.model_validate(resp.json())

    async def approve_task(
        self,
        task_id: UUID,
        decided_by: str = "user",
        reason: str | None = None,
    ) -> ApprovalDecisionResponse:
        """Approve an APPROVE-tier action."""
        req = ApprovalDecision(decided_by=decided_by, reason=reason)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/vision/task/{task_id}/approve",
                json=req.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return ApprovalDecisionResponse.model_validate(resp.json())

    async def deny_task(
        self,
        task_id: UUID,
        decided_by: str = "user",
        reason: str | None = None,
    ) -> ApprovalDecisionResponse:
        """Deny an APPROVE-tier action."""
        req = ApprovalDecision(decided_by=decided_by, reason=reason)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/vision/task/{task_id}/deny",
                json=req.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return ApprovalDecisionResponse.model_validate(resp.json())

    # --- Shadow Desktop ---

    async def shadow_start(
        self,
        resolution: str = "1920x1080x24",
        display_num: int = 99,
    ) -> ShadowStartResponse:
        """Start the shadow desktop."""
        req = ShadowStartRequest(resolution=resolution, display_num=display_num)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/shadow/start",
                json=req.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return ShadowStartResponse.model_validate(resp.json())

    async def shadow_stop(self) -> ShadowStopResponse:
        """Stop the shadow desktop."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/shadow/stop")
            resp.raise_for_status()
            return ShadowStopResponse.model_validate(resp.json())

    async def shadow_health(self) -> ShadowHealthResponse:
        """Check shadow desktop service status."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/shadow/health")
            resp.raise_for_status()
            return ShadowHealthResponse.model_validate(resp.json())

    async def screenshot(self) -> bytes:
        """Capture a screenshot from the shadow desktop (raw PNG bytes)."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/shadow/screenshot")
            resp.raise_for_status()
            return resp.content

    # --- Models ---

    async def models(self) -> ModelsResponse:
        """Get CPU model status and RAM usage."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            return ModelsResponse.model_validate(resp.json())
