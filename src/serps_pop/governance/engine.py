from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from serps_pop.domain.evidence import EvidenceEvent

RULE_VERSION = "CIE-RULES-2.0"
DEFAULT_WINDOW_SECONDS = 60
SUPPORTED_EVENT_TYPES = {
    "camera_connected",
    "camera_disconnected",
    "camera_reconnected",
    "face_detected",
    "face_not_detected",
    "sustained_face_absence",
    "face_detector_unavailable",
    "tab_focus_lost",
    "person_detected",
    "multiple_persons_detected",
    "mobile_phone_detected",
    "object_detector_unavailable",
    "microphone_connected",
    "microphone_disconnected",
    "audio_activity_detected",
    "sustained_audio_activity",
    "audio_monitor_unavailable",
}
RISK_LEVEL_THRESHOLDS = (
    (0.85, "Critical"),
    (0.60, "High"),
    (0.30, "Moderate"),
    (0.00, "Low"),
)
RISK_LEVEL_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}


@dataclass(frozen=True)
class AssessmentResult:
    risk_score: float
    risk_level: str
    confidence: float
    explanation: str
    evidence_window_start: datetime | None
    evidence_window_end: datetime | None
    evidence_event_ids: list[str]
    rule_version: str
    metadata: dict


def risk_level_for_score(score: float) -> str:
    bounded = max(0.0, min(float(score), 1.0))
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if bounded >= threshold:
            return level
    return "Low"


def _contribution(event_type: str, count: int) -> float:
    if event_type == "face_not_detected":
        return 0.60 if count >= 3 else 0.35 if count == 2 else 0.15 if count == 1 else 0.0
    if event_type == "sustained_face_absence":
        return 0.50 if count >= 2 else 0.35 if count == 1 else 0.0
    if event_type == "camera_disconnected":
        return 0.65 if count >= 2 else 0.35 if count == 1 else 0.0
    if event_type == "tab_focus_lost":
        return 0.40 if count >= 3 else 0.20 if count == 2 else 0.10 if count == 1 else 0.0
    if event_type == "multiple_persons_detected":
        return 0.70 if count >= 2 else 0.45 if count == 1 else 0.0
    if event_type == "mobile_phone_detected":
        return 0.75 if count >= 2 else 0.60 if count == 1 else 0.0
    if event_type == "sustained_audio_activity":
        return 0.50 if count >= 3 else 0.35 if count == 2 else 0.15 if count == 1 else 0.0
    if event_type == "audio_activity_detected":
        return 0.10 if count >= 3 else 0.05 if count >= 1 else 0.0
    if event_type == "microphone_disconnected":
        return 0.25 if count >= 2 else 0.10 if count == 1 else 0.0
    return 0.0


def assess_events(events: list[EvidenceEvent], window_seconds: int = DEFAULT_WINDOW_SECONDS) -> AssessmentResult:
    if window_seconds < 1:
        raise ValueError("window_seconds must be at least 1")
    supported = sorted(
        (event for event in events if event.event_type in SUPPORTED_EVENT_TYPES),
        key=lambda item: (item.timestamp, item.event_id),
    )
    if not supported:
        return AssessmentResult(
            risk_score=0.0,
            risk_level="Low",
            confidence=0.0,
            explanation="No supported EvidenceEvents were available in the assessment window; contextual risk remains low.",
            evidence_window_start=None,
            evidence_window_end=None,
            evidence_event_ids=[],
            rule_version=RULE_VERSION,
            metadata={"window_seconds": window_seconds, "event_counts": {}, "combined_pattern": False},
        )

    window_end = supported[-1].timestamp
    window_start = window_end - timedelta(seconds=window_seconds)
    window_events = [event for event in supported if window_start <= event.timestamp <= window_end]
    relevant_types = (
        "face_not_detected",
        "sustained_face_absence",
        "camera_disconnected",
        "tab_focus_lost",
        "multiple_persons_detected",
        "mobile_phone_detected",
        "audio_activity_detected",
        "sustained_audio_activity",
        "microphone_disconnected",
    )
    counts = {event_type: sum(event.event_type == event_type for event in window_events) for event_type in relevant_types}
    score = sum(_contribution(event_type, count) for event_type, count in counts.items())
    correlations: list[str] = []
    # A disconnected camera is a distinct operational condition; it does not
    # corroborate a face-absence observation because no valid frame exists.
    combined = False
    phone_camera_roles = {
        event.camera_id
        for event in window_events
        if event.event_type == "mobile_phone_detected" and event.camera_id
    }
    if len(phone_camera_roles) >= 2:
        score += 0.15
        correlations.append("mobile-phone detection was corroborated across camera roles")
    if (counts["face_not_detected"] >= 2 or counts["sustained_face_absence"] > 0) and counts["sustained_audio_activity"] > 0:
        score += 0.15
        correlations.append("face absence coincided with sustained audio activity")
    if counts["multiple_persons_detected"] > 0 and counts["sustained_audio_activity"] > 0:
        score += 0.20
        correlations.append("multiple persons coincided with sustained audio activity")
    last_face_absence = next(
        (event for event in reversed(window_events) if event.event_type in ("face_not_detected", "sustained_face_absence")),
        None,
    )
    face_recovered = bool(
        last_face_absence
        and any(event.event_type == "face_detected" and event.timestamp > last_face_absence.timestamp for event in window_events)
    )
    score = round(min(score, 1.0), 4)
    contributing = [
        event
        for event in window_events
        if event.event_type in relevant_types and _contribution(event.event_type, counts[event.event_type]) > 0
    ]
    confidence = round(
        sum(event.confidence for event in contributing) / len(contributing) if contributing else 0.25,
        4,
    )

    phrases: list[str] = []
    labels = {
        "face_not_detected": "FACE_NOT_DETECTED",
        "sustained_face_absence": "SUSTAINED_FACE_ABSENCE",
        "camera_disconnected": "CAMERA_DISCONNECTED",
        "tab_focus_lost": "TAB_FOCUS_LOST",
        "multiple_persons_detected": "MULTIPLE_PERSONS_DETECTED",
        "mobile_phone_detected": "MOBILE_PHONE_DETECTED",
        "audio_activity_detected": "AUDIO_ACTIVITY_DETECTED",
        "sustained_audio_activity": "SUSTAINED_AUDIO_ACTIVITY",
        "microphone_disconnected": "MICROPHONE_DISCONNECTED",
    }
    for event_type in relevant_types:
        count = counts[event_type]
        if count:
            noun = "event" if count == 1 else "events"
            phrases.append(f"{count} {labels[event_type]} {noun}")
    duration = max(0, round((window_end - min(event.timestamp for event in window_events)).total_seconds()))
    if phrases:
        explanation = f"{' and '.join(phrases)} occurred within {duration} seconds."
        if combined:
            explanation += " The combined camera-disconnection and face-absence pattern increased contextual risk."
        for correlation in correlations:
            if correlation != "camera disconnection corroborated face absence":
                explanation += f" Corroboration identified: {correlation}."
        repeated = [labels[event_type] for event_type, count in counts.items() if count > 1]
        if repeated:
            explanation += f" Repeated evidence: {', '.join(repeated)}."
        if face_recovered:
            explanation += " A later FACE_DETECTED event records recovery of face presence; prior evidence remains available for human review."
        explanation += f" Deterministic rule {RULE_VERSION} produced a {risk_level_for_score(score)} risk score of {score:.2f}."
    else:
        explanation = "Only non-adverse supported EvidenceEvents occurred in the window; contextual risk remains low."
    unavailable_counts = {
        event_type: sum(event.event_type == event_type for event in window_events)
        for event_type in ("object_detector_unavailable", "audio_monitor_unavailable", "face_detector_unavailable")
    }
    if any(unavailable_counts.values()):
        explanation += " Detector-unavailable states were recorded as operational limitations and did not contribute to misconduct risk."

    # Identity context is separate from aggregate risk. Recovery must follow a
    # sustained primary-camera absence; an arbitrary high score is insufficient.
    sustained = [event for event in window_events
                 if event.event_type == "sustained_face_absence" and event.camera_id in (None, "primary")]
    recovery = next((event for event in reversed(window_events)
                     if sustained and event.event_type == "face_detected"
                     and event.camera_id in (None, "primary") and event.timestamp > sustained[-1].timestamp), None)
    persons = [event for event in window_events if event.event_type == "multiple_persons_detected"]
    identity_context = {}
    for name, context_events, count in (
        ("sustained_absence_reappearance", sustained + ([recovery] if recovery else []), len(sustained) if recovery else 0),
        ("additional_persons", persons, len(persons)),
    ):
        if count:
            identity_context[name] = {
                "count": count, "confidence": min(event.confidence for event in context_events),
                "event_ids": [event.event_id for event in context_events],
                "first_event_at": min(event.timestamp for event in context_events).isoformat(),
            }

    return AssessmentResult(
        risk_score=score,
        risk_level=risk_level_for_score(score),
        confidence=max(0.0, min(confidence, 1.0)),
        explanation=explanation,
        evidence_window_start=window_start,
        evidence_window_end=window_end,
        evidence_event_ids=[event.event_id for event in contributing],
        rule_version=RULE_VERSION,
        metadata={
            "window_seconds": window_seconds,
            "event_counts": counts,
            "combined_pattern": combined,
            "correlations": correlations,
            "face_presence_recovered": face_recovered,
            "identity_context": identity_context,
            "repeated_event_types": [event_type for event_type, count in counts.items() if count > 1],
            "detector_unavailable_counts": unavailable_counts,
        },
    )
