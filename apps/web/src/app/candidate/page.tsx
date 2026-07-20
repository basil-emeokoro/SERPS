"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import {
  acceptCandidateConsent,
  CandidateDashboard,
  fetchCandidateDashboard,
  startCandidateSession,
  submitCameraPermission,
  submitCameraSelection,
  submitDeviceCheck,
  submitEvidenceEvent,
} from "../../lib/api";

function accessToken(): string {
  return sessionStorage.getItem("serps_access_token") ?? "";
}

function browserDetails() {
  const agent = navigator.userAgent;
  const match = agent.match(/(Edg|Chrome|Firefox|Version)\/(\d+)/);
  const browserName = match?.[1] === "Version" ? "Safari" : match?.[1] ?? "Unknown";
  return { browserName, browserVersion: match?.[2] ?? null, supported: ["Edg", "Chrome", "Firefox", "Safari"].includes(browserName) };
}

export default function CandidatePortalPage() {
  const [dashboard, setDashboard] = useState<CandidateDashboard | null>(null);
  const [status, setStatus] = useState("Loading candidate workflow...");
  const [busy, setBusy] = useState(false);
  const [consentChecked, setConsentChecked] = useState(false);
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [selectedCamera, setSelectedCamera] = useState("");
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const refresh = useCallback(async () => {
    const token = accessToken();
    if (!token) return;
    try {
      setDashboard(await fetchCandidateDashboard(token));
      setStatus("Candidate workflow loaded from the live API.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to load candidate workflow.");
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => () => streamRef.current?.getTracks().forEach((track) => track.stop()), []);

  async function acceptConsent() {
    if (!consentChecked) return;
    setBusy(true);
    try {
      await acceptCandidateConsent(accessToken());
      setStatus("Consent version CONSENT-1.0 was recorded immutably.");
      await refresh();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Consent could not be recorded.");
    } finally { setBusy(false); }
  }

  async function runDeviceCheck() {
    setBusy(true);
    try {
      if (!navigator.mediaDevices?.enumerateDevices) throw new Error("Browser media-device APIs are unavailable.");
      const devices = await navigator.mediaDevices.enumerateDevices();
      const details = browserDetails();
      const cameraAvailable = devices.some((device) => device.kind === "videoinput");
      const microphoneAvailable = devices.some((device) => device.kind === "audioinput");
      const result = await submitDeviceCheck(accessToken(), {
        supported_browser: details.supported,
        secure_context: window.isSecureContext,
        camera_available: cameraAvailable,
        microphone_available: microphoneAvailable,
        browser_name: details.browserName,
        browser_version: details.browserVersion,
        operating_system: navigator.platform,
        user_agent: navigator.userAgent,
      }) as { passed: boolean };
      setStatus(result.passed ? "Device compatibility checks passed." : "One or more required device checks failed.");
      await refresh();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Device checks failed.");
    } finally { setBusy(false); }
  }

  async function requestPermissionAndDiscover() {
    setBusy(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      await submitCameraPermission(accessToken(), "granted");
      const devices = await navigator.mediaDevices.enumerateDevices();
      const discovered = devices.filter((device) => device.kind === "videoinput");
      if (!discovered.length) throw new Error("Permission was granted but no camera was discovered.");
      setCameras(discovered);
      setSelectedCamera(discovered[0].deviceId);
      await submitCameraSelection(accessToken(), {
        device_id: discovered[0].deviceId,
        label: discovered[0].label || "Camera",
        group_id: discovered[0].groupId || null,
        camera_count: discovered.length,
      });
      setStatus(`${discovered.length} camera${discovered.length === 1 ? "" : "s"} discovered; permission granted.`);
      await refresh();
    } catch (error) {
      await submitCameraPermission(accessToken(), "denied").catch(() => undefined);
      setStatus(error instanceof Error ? error.message : "Camera permission was not granted.");
    } finally { setBusy(false); }
  }

  async function chooseCamera(deviceId: string) {
    setSelectedCamera(deviceId);
    const camera = cameras.find((item) => item.deviceId === deviceId);
    if (!camera) return;
    await submitCameraSelection(accessToken(), {
      device_id: camera.deviceId,
      label: camera.label || "Camera",
      group_id: camera.groupId || null,
      camera_count: cameras.length,
    });
    const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: true });
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = stream;
    if (videoRef.current) videoRef.current.srcObject = stream;
    await refresh();
  }

  async function beginMonitoring(sessionId: string, candidateId: string) {
    const token = accessToken();
    await submitEvidenceEvent(token, {
      session_id: sessionId, candidate_id: candidateId, event_type: "CAMERA_CONNECTED", description: "Selected browser camera track is live.",
    });
    streamRef.current?.getVideoTracks().forEach((track) => track.addEventListener("ended", () => {
      void submitEvidenceEvent(token, {
        session_id: sessionId, candidate_id: candidateId, event_type: "CAMERA_DISCONNECTED", description: "Browser camera track ended.",
      });
    }, { once: true }));
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) void submitEvidenceEvent(token, {
        session_id: sessionId, candidate_id: candidateId, event_type: "TAB_FOCUS_LOST", description: "Candidate examination tab lost visibility.",
      });
    });

    type Detector = { detect(source: HTMLVideoElement): Promise<unknown[]> };
    const DetectorConstructor = (window as unknown as { FaceDetector?: new () => Detector }).FaceDetector;
    if (DetectorConstructor && videoRef.current) {
      const faces = await new DetectorConstructor().detect(videoRef.current).catch(() => []);
      await submitEvidenceEvent(token, {
        session_id: sessionId,
        candidate_id: candidateId,
        event_type: faces.length ? "FACE_DETECTED" : "FACE_NOT_DETECTED",
        description: faces.length ? "Browser FaceDetector detected a face." : "Browser FaceDetector did not detect a face.",
        confidence: 0.8,
      });
    }
  }

  async function startExam(examinationId: string) {
    setBusy(true);
    try {
      if (!streamRef.current?.getVideoTracks().some((track) => track.readyState === "live")) {
        throw new Error("A live camera stream is required before starting the examination.");
      }
      const session = await startCandidateSession(accessToken(), examinationId);
      await beginMonitoring(session.session_id, session.candidate_id);
      setStatus("Examination session started. Live browser evidence is flowing into governance.");
      await refresh();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Examination could not start.");
    } finally { setBusy(false); }
  }

  return (
    <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Complete consent and real browser/device checks before starting an assigned examination.">
      <p className="workflow-status">{status}</p>
      <section className="status-grid">
        <article className="card"><span className="badge">Assignments</span><h2>Assigned examinations</h2>
          {dashboard?.assigned_examinations.length ? dashboard.assigned_examinations.map((exam) => (
            <div className="assignment" key={exam.assignment_id}><strong>{exam.title}</strong><span>{exam.exam_code} · {exam.duration_minutes} minutes</span>
              <button disabled={busy || !dashboard.readiness.ready_to_start} onClick={() => void startExam(exam.examination_id)}>Start examination</button></div>
          )) : <p>No assigned examinations are currently available.</p>}
        </article>
        <article className="card"><span className="badge">Consent</span><h2>Required agreements</h2>
          <label className="check-row"><input type="checkbox" checked={consentChecked} onChange={(event) => setConsentChecked(event.target.checked)} />I accept monitoring, the privacy notice, and institutional examination policy.</label>
          <button disabled={busy || !consentChecked} onClick={() => void acceptConsent()}>Accept consent</button>
          <p>{dashboard?.consent?.accepted ? `Accepted (${dashboard.consent.consent_version})` : "Valid consent required"}</p>
        </article>
        <article className="card"><span className="badge">Device</span><h2>Compatibility check</h2>
          <button disabled={busy} onClick={() => void runDeviceCheck()}>Run browser checks</button>
          <p>{dashboard?.device_check?.passed ? `Passed in ${dashboard.device_check.browser_name}` : "Not passed"}</p>
        </article>
        <article className="card"><span className="badge">Camera</span><h2>Discovery and permission</h2>
          <button disabled={busy} onClick={() => void requestPermissionAndDiscover()}>Request camera and microphone</button>
          {cameras.length > 0 && <select value={selectedCamera} onChange={(event) => void chooseCamera(event.target.value)}>{cameras.map((camera) => <option key={camera.deviceId} value={camera.deviceId}>{camera.label || "Camera"}</option>)}</select>}
          <video ref={videoRef} autoPlay muted playsInline />
          <p>{dashboard?.camera_permission?.granted ? `${dashboard.camera_selection?.camera_count ?? 0} camera(s), permission granted` : "Camera permission required"}</p>
        </article>
      </section>
      <section className="card readiness-card"><h2>Session readiness</h2><div className="state-list">
        {Object.entries(dashboard?.readiness ?? {}).map(([name, passed]) => <span className={passed ? "state-pass" : "state-fail"} key={name}>{name.replaceAll("_", " ")}: {passed ? "pass" : "fail"}</span>)}
      </div></section>
    </PortalShell>
  );
}
