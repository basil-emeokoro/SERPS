"""Operational camera context, separate from identity or misconduct findings."""
from typing import Literal

from pydantic import BaseModel

from serps_pop.domain.evidence import EvidenceEvent

CAMERA_LOSS_ACTIONS = {"CONTINUE_MONITORING", "NOTIFY_REVIEWER", "PROTECT_AND_PAUSE"}


def camera_condition(events: list[EvidenceEvent], mode: str) -> dict:
    required = ["primary", "secondary"] if mode == "B" else ["primary"]
    latest = {}
    for event in sorted(events, key=lambda item: (item.timestamp, item.event_id)):
        role = event.camera_id or "primary"
        if role in required and event.event_type in {"camera_connected", "camera_reconnected", "camera_disconnected"}:
            latest[role] = event
    unavailable = [role for role in required if role in latest and latest[role].event_type == "camera_disconnected"]
    return {"deployment_mode": mode, "required_roles": required, "unavailable_roles": unavailable,
            "event_ids": [latest[role].event_id for role in unavailable], "misconduct_determination": False}


def camera_loss_action(metadata: dict, condition: dict) -> str | None:
    action = metadata.get("required_camera_loss_action")
    return action if condition.get("unavailable_roles") and action in CAMERA_LOSS_ACTIONS else None


class CameraMonitoringPolicy(BaseModel):
    required_camera_loss_action: Literal["CONTINUE_MONITORING", "NOTIFY_REVIEWER", "PROTECT_AND_PAUSE"] | None = None
