# SERPS Proctoring Modes Implementation Status

Validation date: 2026-08-01  
Scope: bounded research-prototype object and audio monitoring

## Shared rules

- Object inference is local browser inference using EfficientDet-Lite0 COCO float32/1, sampled every 1.5 seconds with a default 0.55 confidence threshold.
- Audio monitoring is available once per active session in every mode through a local Web Audio RMS monitor.
- Raw video and raw audio are not persisted by default. Reviewers receive structured metadata, not a remote live-media feed.
- A missing, disconnected or unavailable detector is an observation-quality limitation. It does not add misconduct risk and cannot terminate an examination.
- CIE scores evidence only when an event is present and distinguishes isolated, repeated, corroborated and unavailable states.

## Mode matrix

| Mode | Intended arrangement | Object-inference feeds | Audio | Secondary/mirror limitations | CIE treatment | Verified status |
| --- | --- | --- | --- | --- | --- | --- |
| A | One candidate-facing camera | Primary only | Available | No independent secondary evidence is expected | No penalty for absent secondary evidence | Routing tests pass; physical integrated-camera person inference passed |
| B | Distinct primary candidate camera and secondary environment camera | Primary and secondary | Available once per session | Corroboration requires both configured tracks | Cross-role phone evidence increases corroboration; unavailable role remains neutral | Routing/correlation tests pass; full physical dual-camera rerun pending |
| C | One camera plus a physical mirror | Primary only | Available | Mirror is part of the same image, not an independent digital feed | No secondary-confidence bonus; missing secondary remains neutral | Routing tests pass; live mirror-assisted rerun pending |

## Current setup limitation

Candidate readiness retains the existing dual-camera selection and distinct-device prerequisites before starting a new session, including Modes A and C. Once a session exists, detector routing is mode-correct. This prerequisite is a documented prototype limitation and was not redesigned here.

The 2026-08-01 Mode A session was pinned to an older USB-camera device identifier. Only the integrated camera was exposed by the validation browser, so normal workspace acquisition reported permission denied instead of silently changing cameras. A controlled diagnostic attached the available integrated camera to the loaded detector and produced genuine person detections. Before a defence demonstration, return to Device Readiness, reconnect/reselect intended devices and create a fresh session.

## Claims boundary

Supported: local mode-aware routing, physical Mode A person inference, Mode A audio availability, neutral missing-modality handling, and controlled Mode B/C correlation tests.

Not supported: a claim that all modes are physically validated on the defence hardware, that a mirror equals a second independent camera, or that unavailable secondary evidence proves misconduct.
