# Sprint 4C Local Face Detection Report

## Selected implementation

SERPS uses `@mediapipe/tasks-vision` 0.10.35 and the MediaPipe Face Landmarker float16 task bundle. The detector was selected because it runs synchronously on local browser video frames, returns 478 normalized landmarks for each detected face, supports explicit multi-face limits, and has maintained WebAssembly browser support. MediaPipe's repository and browser samples are Apache-2.0 licensed.

The application serves every runtime dependency from its own origin:

- npm runtime: `@mediapipe/tasks-vision` 0.10.35;
- model: `public/mediapipe/models/face_landmarker.task` (3,758,596 bytes);
- model SHA-256: `64184E229B263107BC2B804C6625DB1341FF2BB731874B0BCC2FE6544E0BC9FF`;
- WebAssembly loaders and binaries: `public/mediapipe/wasm`;
- model source: Google's official MediaPipe model storage;
- software licence: Apache License 2.0.

No CDN URL, remote model URL, browser experimental flag, or native `FaceDetector` API is used. The CPU delegate is selected for predictable dissertation-machine compatibility.

## Detector abstraction

`LocalFaceLandmarker` exposes readiness, face count, normalized bounding box, landmarks, centre, area, bounded yaw/pitch proxies, roll estimate, and processing time. MediaPipe Face Landmarker does not expose a calibrated per-face confidence in this API, so `confidence` remains `null` at the detector boundary rather than being fabricated. The enrolment quality confidence is separately and explicitly derived from lighting and face-size checks.

Yaw and pitch are geometric proxies derived from nose position within the detected face bounds. Roll is estimated from eye landmarks. These values guide the research-prototype workflow; they are not calibrated head-pose angles.

## Enrolment and liveness controls

The enrolment screen continuously analyses the real video element and distinguishes zero, one, and multiple faces. A capture requires:

- exactly one face;
- acceptable lighting and face size;
- roll within the bounded threshold;
- the requested forward, left, right, up, down, or centre orientation;
- a continuous 900 ms correct-pose hold.

The backend issues an unpredictable three-action liveness order. The client validates the corresponding orientation for each action, while the backend rejects wrong order, intervals below 350 ms, or a total sequence below one second. This prevents a single static frame or rapid repeated click from satisfying the sequence, but it is not certified presentation-attack detection.

## Representation and privacy boundary

Raw frames remain in the browser and are not uploaded or persisted. Once the face bounds are known, SERPS derives a 64-value luminance summary for bounded prototype similarity. This 8-by-8 summary is deliberately labelled experimental and is not a biometric-grade face embedding.

MediaPipe's upstream privacy notice states that task input processing occurs on-device and input data is not sent to Google, while also describing product metrics collection. SERPS therefore validates browser network traffic for this build and records whether any non-local request occurs. Institutional deployment would still require legal/privacy review, informed consent, retention controls, and a production-grade biometric design.

## Validation record

- TypeScript type check: passed.
- ESLint: passed; generated MediaPipe Emscripten files are excluded as third-party vendor output.
- Frontend tests: 23 passed.
- Focused backend identity tests: 4 passed.
- Production compile: passed.
- Real Edge camera, zero/one/multiple-face, all six physical directions, liveness movement, and external-network observation: recorded separately after the synchronized repository build is deployed.

No successful physical result is claimed until a person and the required camera conditions have been observed in Microsoft Edge.

## Sources

- MediaPipe repository and privacy notice: https://github.com/google-ai-edge/mediapipe
- MediaPipe Apache-2.0 licence: https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE
- MediaPipe browser samples: https://github.com/google-ai-edge/mediapipe-samples-web
