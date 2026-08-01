# Sprint 4C Runtime Reactivity

## Update mechanism

SERPS continues to use its existing HTTP and append-only EvidenceEvent architecture. Sprint 4C adds bounded polling rather than a competing event bus:

- candidate browser device state reacts immediately to `MediaStreamTrack` `ended`, `mute` and `unmute` signals and the `mediaDevices.devicechange` event;
- active candidate camera tracks create privacy-safe heartbeat EvidenceEvents every 15 seconds;
- a connect, disconnect or reconnect event passes through the existing contextual assessment, advisory recommendation and institutional policy pipeline;
- reviewer, administrator and session-detail projections poll every 10 seconds and retain explicit last-update/freshness information;
- backend camera projections treat a connected/heartbeat event older than 35 seconds as **unavailable**, not connected.

No raw video or image is uploaded by this mechanism.

## Defence frontend startup

The defence interface must use the production build, which does not include the Next.js development badge, issue counter or development overlay:

```powershell
cd C:\SERPS\apps\web
npm.cmd run build
npm.cmd run start -- --hostname localhost --port 3100
```

Run the API separately on its configured port (currently 8010). The frontend `NEXT_PUBLIC_API_BASE_URL` must point to that API before `npm.cmd run build` is executed.

## Face-detection boundary

Camera acquisition is independent of face-detector capability. The tested Microsoft Edge installation can open and preview the integrated camera, but does not expose the experimental native `FaceDetector` API. SERPS therefore reports camera active and detector unavailable as separate facts and does not permit pose acceptance or simulate a face result. A locally bundled, licensed detector and model assets remain required before non-demo facial enrolment can be completed reliably across supported browsers.
