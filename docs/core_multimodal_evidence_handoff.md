# Core Multimodal Evidence Handoff

Workspace B may use this document to refine dissertation claims. It must not elevate fixture or automated results into physical-device results.

## Exact status

- Local object detector: operational. MediaPipe Tasks Vision 0.10.35 loads local EfficientDet-Lite0 COCO float32/1 weights from `/mediapipe/models/efficientdet_lite0.tflite`; SHA-256 `40338EDF5EC70D43E318B0A716A84D4564CD1802759A7A07170C7E43796DBF58`.
- Person: physically runtime-validated on the integrated camera; persisted confidence values 0.781 and 0.7506.
- Multiple persons and mobile phone: implemented and end-to-end fixture-tested; physical observations pending.
- Audio: physical microphone acquisition and live RMS processing validated; no physical threshold-crossing or sustained sound event was generated.
- Governance: object/audio events traverse EvidenceEvent, CIE, Agentic recommendation, IPIME, reviewer metadata, governance audit and report. Examination continuation and human reviewer authority are preserved.

## Evidence locations

| Area | Paths |
| --- | --- |
| Object inference | `apps/web/src/lib/objectDetection.ts`; `apps/web/public/mediapipe/models/efficientdet_lite0.tflite`; `apps/web/public/mediapipe/wasm/` |
| Audio analysis | `apps/web/src/lib/audioMonitoring.ts` |
| Event mapping and modes | `apps/web/src/lib/multimodalEvents.ts` |
| Candidate integration | `apps/web/src/app/candidate/examinations/[sessionId]/page.tsx` |
| Contract and persistence | `src/serps_pop/domain/evidence.py`; `src/serps_pop/evidence/`; `POST /api/v1/evidence-events/` |
| Migration | `migrations/versions/0008_core_multimodal_evidence.py` |
| CIE/Agentic/IPIME | `src/serps_pop/governance/engine.py`; `src/serps_pop/governance/services.py` |
| Reviewer/admin/report | `apps/web/src/components/SessionOperationalView.tsx`; reviewer/admin session routes; report endpoints |
| Tests | `apps/web/src/lib/multimodal.test.ts`; `tests/test_multimodal.py` |

## Supported event types

`person_detected`, `multiple_persons_detected`, `mobile_phone_detected`, `object_detector_unavailable`, `microphone_connected`, `microphone_disconnected`, `audio_activity_detected`, `sustained_audio_activity`, and `audio_monitor_unavailable`.

The existing candidate-authorised, institution-scoped EvidenceEvent API persists class, count, confidence, model/detector version, threshold, camera role, normalised RMS level, duration, recurrence and correlation metadata. Raw image/frame/audio keys are rejected.

## Test and runtime results

- Full backend: 63 passed in 210.61 seconds; focused multimodal backend: 8 passed.
- Full frontend: 35 passed across four files; focused multimodal frontend: 10 passed.
- TypeScript, ESLint, Python compilation and Next.js production build: passed.
- SQLite and PostgreSQL: both at `0008_core_multimodal_evidence` head.
- SQLite controlled fixture: persistence, High CIE result, `NOTIFY_REVIEWER`, reviewer visibility, governance audit and report inclusion passed.
- PostgreSQL controlled fixtures: four events persisted/retrieved; reviewer/report inclusion passed; CIE Critical; `ESCALATE_INCIDENT`; `continue_examination=true`; session active; governance audit persisted.
- Physical browser: local model/WASM HTTP 200, graph started, no failed/external inference requests, integrated camera 640×480/30 fps, genuine person detections persisted, Realtek microphone acquired and live RMS displayed.
- Physical limitation: the active session referenced a stale/disconnected USB-camera identifier; normal acquisition was denied and did not switch cameras silently. Physical multi-person, phone and above-threshold sound cases remain pending.
- Dependency audit: three high-severity advisory groups remain; no forced out-of-range dependency update was made.

## Dissertation wording

### Claims that can remain

- SERPS performs bounded local browser object inference for person and COCO cell-phone classes using locally hosted assets.
- SERPS derives privacy-safe normalised audio energy without storing or transcribing raw audio by default.
- Structured multimodal evidence is persisted and processed through explainable deterministic contextual rules.
- Recommendations remain advisory, institutional policy is evaluated, examinations continue, and final authority remains with a human reviewer.
- Reviewer and administrator interfaces expose metadata and explanations rather than simulated remote media feeds.

### Claims requiring qualification

- Multiple-person and mobile-phone capabilities have automated and controlled-fixture evidence, but physical validation is pending.
- Audio activity/sustained-activity logic is tested; physical microphone acquisition, not a threshold-crossing event, was observed.
- Mode routing is automated for A/B/C; physical runtime validation is complete only for Mode A.
- EfficientDet-Lite0 is a research-prototype component; no SERPS-specific accuracy, fairness or robustness benchmark exists.

### Claims that must be removed

- Arbitrary prohibited-object or complete environmental understanding claims.
- Speaker identification, multiple-speaker recognition, transcription, prohibited-word detection or semantic conversation analysis.
- Certified accuracy, production surveillance readiness, remote live-video streaming, or automatic misconduct determination/termination.

## Authentic figure and evaluation proposals

Chapter Four screenshots: candidate workspace showing model ready, local person count and privacy notice; reviewer event metadata; CIE explanation; Agentic recommendation; IPIME outcome; governance timeline; generated report entry. Label controlled fixtures and do not present them as physical detections.

Chapter Five tables/charts: detector configuration; event schema and retention boundary; isolated/repeated/corroborated rule table; automated-test matrix; SQLite/PostgreSQL comparison; physical/fixture/unvalidated matrix; inference-time samples; limitations table. Do not construct an accuracy/confusion matrix without a real labelled dataset.

## Statements that must not be made

Do not state that SERPS identifies cheating, understands speech, distinguishes speakers, detects every phone/person, streams live feeds, has certified accuracy, physically validates every mode/event, or automatically stops/fails an examination.
