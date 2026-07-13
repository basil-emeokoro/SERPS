from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_api_health() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_evidence_event() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/evidence-events/",
        json={
            "session_id": "SESSION-001",
            "candidate_id": "CAND-001",
            "source_module": "visual_intelligence",
            "event_type": "face_present",
            "risk_weight": 0.01,
            "confidence": 0.99,
            "description": "Face visible in primary camera.",
            "camera_id": "primary",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"].startswith("EVT-")
    assert body["event_type"] == "face_present"
