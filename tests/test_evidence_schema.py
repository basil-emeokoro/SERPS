from serps_pop.domain.evidence import EvidenceEvent, EvidenceEventCreate


def test_evidence_event_preserves_poc_risk_points_contract() -> None:
    event = EvidenceEvent.from_create(
        EvidenceEventCreate(
            session_id="SESSION-001",
            candidate_id="CAND-001",
            source_module="Primary Camera",
            event_type="Camera Stream Ready",
            risk_weight=0.02,
            confidence=0.95,
            description="Primary stream is ready.",
            camera_id="primary",
        )
    )

    assert event.event_id.startswith("EVT-")
    assert event.source_module == "primary_camera"
    assert event.event_type == "camera_stream_ready"
    assert event.risk_points() == 2
