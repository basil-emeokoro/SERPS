# Sprint 4C State Reactivity Audit

Audit date: 22 July 2026  
Scope: public, authentication, registration, enrolment, candidate, reviewer, administrator, system-administrator and monitored-session interfaces.  
Classification reflects the implementation at the start of Sprint 4C, before remediation.

## Classification key

- **Live** — derived from the current browser or backend state at the time it is shown.
- **Polled** — refreshed from the backend on a bounded interval.
- **Event-driven** — updated in response to a browser or application event.
- **Seeded demonstration data** — comes from the documented demonstration fixture.
- **Hard-coded** — embedded in frontend code or copy.
- **Stale** — once-live data with no adequate refresh or freshness threshold.
- **Unavailable** — the implementation cannot currently establish the value truthfully.

## Audit register

| Page/component | Displayed field | Current data source | Expected live data source | Refresh mechanism required | Classification before Sprint 4C |
|---|---|---|---|---|---|
| Landing page | Service health | `/api/v1/health` | Current API health | Explicit refresh and timestamp | Live, loaded once |
| Landing page | Governance-stage descriptions | Frontend constants | Explanatory product content | None; identify as explanatory content | Hard-coded |
| Landing page | Supported session states/version | Frontend constants | Released product metadata | Build/release configuration | Hard-coded |
| Login | Default institution and email | Component initial state (`MIVA`, admin demo account) | Empty deterministic form or user input | User input | Seeded demonstration data presented as default |
| Login | Demonstration-account indicator | Email component state during render | Deterministic mounted client state | User input after hydration | Hydration risk |
| Registration | Institution | Text input defaulted to `MIVA` | Public active-institution configuration endpoint | Load on entry; retry on failure | Hard-coded |
| Registration | Candidate fields | Candidate identifier/name/email constants in JSX | Institution registration configuration and version | Reload when institution/account type changes | Hard-coded |
| Registration | Verification/account state | Registration response | Backend registration lifecycle | Action response; later portal refresh | Live after submit |
| Enrolment | Required liveness actions | Session storage challenge | Backend-issued challenge | Loaded once for bounded challenge | Live challenge state, client-cached |
| Enrolment | Camera active | Presence of attempted stream only | Current `MediaStreamTrack.readyState`, mute/end events | Event-driven | Unavailable when detector unsupported |
| Enrolment | Face count/pose | Experimental `window.FaceDetector` | Locally bundled detector or supported native capability | Repeated browser-frame analysis | Unavailable in tested Edge |
| Enrolment | Lighting/distance | Pixel analysis inside native face box | Current video frame and detected face box | Repeated browser-frame analysis | Live only when native detector exists; otherwise static 0% |
| Enrolment | Capture progress/retries | React state | Current enrolment interaction | Event-driven | Live |
| Candidate portal | Assigned examinations/readiness | Candidate dashboard endpoint | Current backend candidate workflow state | Bounded polling plus manual refresh | Live, loaded once and becomes stale |
| Candidate portal | Camera choices | `enumerateDevices()` after permission | Current browser device inventory | `devicechange` plus explicit refresh | Live at discovery time |
| Candidate portal | Camera readiness | Saved backend selections/permissions | Browser devices plus current tracks and backend readiness | Event-driven locally; persisted events | Mixed live and stale |
| Candidate session | Camera connected state | Local `getUserMedia` result | Active track plus device inventory | `ended`, `mute`, `unmute`, `devicechange` | Event-driven, partial |
| Candidate session | Last-seen/freshness | Not displayed locally | Candidate heartbeat/event acknowledgement | Bounded heartbeat | Unavailable |
| Candidate session | Assessment questions | Frontend demonstration fixture | Deliberate demonstration harness | None; label as demonstration fixture | Seeded demonstration data |
| Candidate session | Elapsed time | Backend `started_at` plus `Date.now()` after mount | Current browser clock relative to persisted start | One-second client timer | Live after mount |
| Candidate session | Governance state | Not displayed/refetched in candidate workspace | Backend evidence/governance pipeline | Poll after device event | Unavailable |
| Reviewer queue | Session/risk/recommendation/policy | Reviewer queue endpoint | Current backend operational projection | Bounded polling and manual refresh | Live, loaded once and becomes stale |
| Reviewer queue | Camera status | Latest historical camera metadata | Current session projection using event freshness threshold | Candidate heartbeat plus polling | Stale; may report connected from historical event |
| Reviewer session | Identity, evidence and governance | Operational session endpoint | Current backend session projection | Bounded polling and manual refresh | Live, loaded once and becomes stale |
| Reviewer session | Timeline labels | Raw entity/event types | Backend records formatted for human review | Refresh with session projection | Live data, developer-oriented presentation |
| Administrator | Metrics/risk distribution | Admin metrics endpoint | Current backend projection with freshness threshold | Bounded polling and manual refresh | Live, loaded once; camera counts may be stale |
| Administrator | Camera failure/unresolved counts | Historical/current mixed backend query | Current active sessions and fresh latest device events | Bounded polling | Potentially stale |
| Administrator | Recent audit activity | Backend audit rows | Current audit records | Bounded polling | Live, loaded once |
| Administrator | Policy | Admin policy endpoint | Active institution policy | Bounded polling/manual refresh | Live, loaded once |
| System administrator | Registration queue/status | Registration endpoint | Current registration lifecycle | Bounded polling/manual refresh | Live, loaded once |
| System administrator | Institution configuration | Not displayed | Active backend configuration and versions | Load, edit/version, refresh | Unavailable |
| Global navigation | Open/closed state | React state | Current interaction | Event-driven | Live, but missing complete focus management |
| Global layout | Environment/version/footer | Partial landing-page constants | public runtime/build metadata | Build configuration | Hard-coded/partly unavailable |

## Priority conclusions

1. A deterministic first render and mounted-only demonstration indicator are required on login.
2. Public institution and versioned field configuration must replace the MIVA-only registration shape, with matching server validation and persisted submissions.
3. Enrolment must open the camera independently of detector availability. Detector capability, camera availability and face/pose results must be represented as separate states.
4. Candidate device state must be driven by media-track and `devicechange` events and persisted as timestamped EvidenceEvents/heartbeats.
5. Reviewer and administrator projections require bounded polling and a freshness threshold; historical `camera_connected` events alone cannot mean currently connected.
6. Governance and timeline displays must refresh after current events and translate technical identifiers without discarding inspector details.
7. Deliberate fixtures (demonstration questions, demo accounts and seeded examinations) must remain clearly labelled and must never be described as live production data.
