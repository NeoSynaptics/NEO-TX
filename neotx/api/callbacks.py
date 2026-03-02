"""Callback endpoints — Alchemy calls these to communicate with NEO-TX.

Approval requests, notifications, and task updates flow through here.
All responses are stubs (Phase 0) — just acknowledge receipt.
"""

from __future__ import annotations

from fastapi import APIRouter

from neotx.schemas import (
    ApprovalRequest,
    ApprovalRequestAck,
    NotifyAck,
    NotifyRequest,
    TaskUpdateAck,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/callbacks", tags=["callbacks"])


@router.post("/approval", response_model=ApprovalRequestAck)
async def receive_approval_request(req: ApprovalRequest) -> ApprovalRequestAck:
    """Alchemy asks: user needs to approve this action before it executes."""
    # Phase 0: acknowledge only. Phase 3+ shows dialog to user.
    return ApprovalRequestAck(received=True, task_id=req.task_id)


@router.post("/notify", response_model=NotifyAck)
async def receive_notification(req: NotifyRequest) -> NotifyAck:
    """Alchemy notifies: a NOTIFY-tier action was executed."""
    # Phase 0: acknowledge only. Phase 4+ shows tray notification.
    return NotifyAck(received=True)


@router.post("/task-update", response_model=TaskUpdateAck)
async def receive_task_update(req: TaskUpdateRequest) -> TaskUpdateAck:
    """Alchemy reports: task status changed (running, completed, failed)."""
    # Phase 0: acknowledge only. Phase 3+ updates task list UI.
    return TaskUpdateAck(received=True)
