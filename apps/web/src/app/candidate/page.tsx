"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import { ErrorState, LoadingState, ReadinessSummary, StatusBadge } from "../../components/OperationalStates";
import { acceptCandidateConsent, CandidateDashboard, fetchCandidateDashboard, startCandidateSession, submitCameraPermission, submitCameraSelection, submitDeviceCheck } from "../../lib/api";
import { validateCameraPair } from "../../lib/operational";

function browserDetails() {
  const match = navigator.userAgent.match(/(Edg|Chrome|Firefox|Version)\/(\d+)/);
  const name = match?.[1] === "Version" ? "Safari" : match?.[1] ?? "Unknown";
  return { name, version: match?.[2] ?? null, supported: ["Edg", "Chrome", "Firefox", "Safari"].includes(name) };
}

export default function CandidatePortalPage() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<CandidateDashboard | null>(null);
  const [status, setStatus] = useState("Loading candidate workflow...");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [consentChecked, setConsentChecked] = useState(false);
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [primaryId, setPrimaryId] = useState("");
  const [secondaryId, setSecondaryId] = useState("");
  const primaryStream = useRef<MediaStream | null>(null);
  const secondaryStream = useRef<MediaStream | null>(null);
  const primaryVideo = useRef<HTMLVideoElement | null>(null);
  const secondaryVideo = useRef<HTMLVideoElement | null>(null);

  const refresh = useCallback(async (signal?: AbortSignal) => {
    await Promise.resolve();
    try { setDashboard(await fetchCandidateDashboard(signal)); setError(""); }
    catch (reason) { if (!(reason instanceof DOMException && reason.name === "AbortError")) setError(reason instanceof Error ? reason.message : "Unable to load candidate workflow."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const controller = new AbortController(); const task = window.setTimeout(() => void refresh(controller.signal), 0); return () => { window.clearTimeout(task); controller.abort(); }; }, [refresh]);
  useEffect(() => () => [...(primaryStream.current?.getTracks() ?? []), ...(secondaryStream.current?.getTracks() ?? [])].forEach((track) => track.stop()), []);

  async function acceptConsent() {
    if (!consentChecked) return;
    setBusy(true);
    try { await acceptCandidateConsent(); setStatus("Consent version CONSENT-1.0 recorded as a new immutable record."); await refresh(); }
    catch (reason) { setStatus(reason instanceof Error ? reason.message : "Consent could not be recorded."); }
    finally { setBusy(false); }
  }

  async function discoverDevices() {
    setBusy(true);
    try {
      if (!navigator.mediaDevices?.enumerateDevices || !navigator.mediaDevices.getUserMedia) throw new Error("This browser does not expose required media-device APIs.");
      const permissionStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      permissionStream.getTracks().forEach((track) => track.stop());
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter((device) => device.kind === "videoinput");
      const details = browserDetails();
      const result = await submitDeviceCheck({ supported_browser: details.supported, secure_context: window.isSecureContext, camera_available: videoDevices.length > 0, microphone_available: devices.some((device) => device.kind === "audioinput"), browser_name: details.name, browser_version: details.version, operating_system: navigator.platform, user_agent: navigator.userAgent }) as { passed: boolean };
      setCameras(videoDevices);
      setPrimaryId(videoDevices[0]?.deviceId ?? "");
      setSecondaryId(videoDevices[1]?.deviceId ?? "");
      setStatus(videoDevices.length >= 2 ? `${videoDevices.length} cameras discovered. Select and preview both roles.` : "Only one camera was discovered. Dual-camera readiness cannot be achieved on this device.");
      if (!result.passed) setStatus("One or more required browser/device checks failed.");
      await refresh();
    } catch (reason) {
      await Promise.all([submitCameraPermission("primary", "denied").catch(() => undefined), submitCameraPermission("secondary", "denied").catch(() => undefined)]);
      setStatus(reason instanceof Error ? reason.message : "Camera and microphone permission was denied.");
    } finally { setBusy(false); }
  }

  async function previewCamera(role: "primary" | "secondary") {
    const deviceId = role === "primary" ? primaryId : secondaryId;
    const pairError = validateCameraPair(primaryId, secondaryId);
    if (pairError) { setStatus(pairError); return; }
    const device = cameras.find((item) => item.deviceId === deviceId);
    setBusy(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
      const streamRef = role === "primary" ? primaryStream : secondaryStream;
      const videoRef = role === "primary" ? primaryVideo : secondaryVideo;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      await submitCameraSelection({ camera_role: role, device_id: deviceId, label: device?.label || `${role} camera`, group_id: device?.groupId || null, camera_count: cameras.length });
      await submitCameraPermission(role, "granted");
      setStatus(`${role === "primary" ? "Primary" : "Secondary"} camera preview is live.`);
      await refresh();
    } catch (reason) {
      await submitCameraPermission(role, "denied").catch(() => undefined);
      setStatus(reason instanceof Error ? reason.message : `${role} camera permission denied.`);
    } finally { setBusy(false); }
  }

  async function startExam(examinationId: string) {
    const pairError = validateCameraPair(primaryId, secondaryId);
    if (pairError) { setStatus(pairError); return; }
    if (!primaryStream.current?.active || !secondaryStream.current?.active) { setStatus("Both live camera previews are required before session start."); return; }
    setBusy(true);
    try {
      const session = await startCandidateSession(examinationId);
      primaryStream.current.getTracks().forEach((track) => track.stop());
      secondaryStream.current.getTracks().forEach((track) => track.stop());
      router.push(`/candidate/examinations/${session.session_id}`);
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : "Examination could not start."); setBusy(false); }
  }

  if (loading) return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Preparing the candidate workflow."><LoadingState /></PortalShell>;
  if (error) return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Candidate workflow unavailable."><ErrorState message={error} onRetry={() => { setLoading(true); void refresh(); }} /></PortalShell>;

  return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Complete consent and verified dual-camera setup before entering the bounded demonstration examination workspace.">
    <p className="workflow-status" role="status" aria-live="polite">{status}</p>
    {dashboard?.active_session && <section className="card active-session"><StatusBadge label="Active demonstration" tone="success" /><h2>Resume monitored workspace</h2><Link className="button-link" href={`/candidate/examinations/${dashboard.active_session.session_id}`}>Open demonstration workspace</Link></section>}
    <section className="status-grid">
      <article className="card"><span className="badge">Assigned examinations</span><h2>Available demonstrations</h2>{dashboard?.assigned_examinations.length ? dashboard.assigned_examinations.map((exam) => <div className="assignment" key={exam.assignment_id}><strong>{exam.title}</strong><span>{exam.exam_code} · {exam.duration_minutes} minutes</span><button disabled={busy || !dashboard.readiness.ready_to_start} onClick={() => void startExam(exam.examination_id)}>Start demonstration</button></div>) : <p>No assigned examinations are available.</p>}</article>
      <article className="card"><span className="badge">Consent</span><h2>Required agreements</h2><label className="check-row"><input type="checkbox" checked={consentChecked} onChange={(event) => setConsentChecked(event.target.checked)} />I accept monitoring, the privacy notice, and institutional examination policy.</label><button disabled={busy || !consentChecked} onClick={() => void acceptConsent()}>Accept consent</button><p>{dashboard?.consent?.accepted ? `Accepted (${dashboard.consent.consent_version})` : "Valid consent required"}</p></article>
    </section>
    <section className="card camera-setup"><div className="section-heading"><div><span className="badge">Mandatory dual-camera setup</span><h2>Candidate-facing and environmental views</h2></div><button disabled={busy} onClick={() => void discoverDevices()}>Discover cameras and check device</button></div>{cameras.length < 2 && <div className="inline-warning" role="alert">Dual-camera readiness unavailable: connect a second video-input device, then retry discovery.</div>}<div className="dual-camera-grid">{(["primary", "secondary"] as const).map((role) => { const selected = role === "primary" ? primaryId : secondaryId; return <article className="camera-panel setup-panel" key={role}><h3>{role === "primary" ? "Primary camera" : "Secondary camera"}</h3><p>{role === "primary" ? "Candidate-facing view: face and upper body" : "Room, desk, side-angle or wider environmental view"}</p><select aria-label={`${role} camera device`} value={selected} onChange={(event) => role === "primary" ? setPrimaryId(event.target.value) : setSecondaryId(event.target.value)}><option value="">Select {role} camera</option>{cameras.map((camera) => <option value={camera.deviceId} key={camera.deviceId}>{camera.label || `Camera ${cameras.indexOf(camera) + 1}`}</option>)}</select><button disabled={busy || !selected} onClick={() => void previewCamera(role)}>Preview {role} camera</button><video ref={role === "primary" ? primaryVideo : secondaryVideo} autoPlay muted playsInline aria-label={`${role} camera local preview`} /></article>; })}</div><p className="privacy-note">Camera previews are local to this browser. SERPS persists operational metadata and EvidenceEvents, not raw video.</p></section>
    <section className="card readiness-card"><h2>Session readiness</h2><ReadinessSummary readiness={dashboard?.readiness ?? {}} /></section>
  </PortalShell>;
}
