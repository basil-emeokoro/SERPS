"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import { ErrorState, LoadingState, ReadinessSummary, StatusBadge } from "../../components/OperationalStates";
import { acceptCandidateConsent, CandidateDashboard, fetchCandidateDashboard, startCandidateSession, submitCameraPermission, submitCameraSelection, submitDeviceCheck } from "../../lib/api";
import { cameraLabel, persistCameraRoles, readCameraRoles, recommendCameraRoles } from "../../lib/cameraRoles";
import { classifyMediaError, discoverVideoDevices, stopMediaStream } from "../../lib/mediaDevices";
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
  const [actionStatus, setActionStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [consentChecked, setConsentChecked] = useState(false);
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [primaryId, setPrimaryId] = useState("");
  const [secondaryId, setSecondaryId] = useState("");
  const [rolesConfirmed, setRolesConfirmed] = useState(false);
  const [mirrorConfirmed, setMirrorConfirmed] = useState(false);
  const [roleReason, setRoleReason] = useState("Discover cameras to assign semantic roles.");
  const primaryStream = useRef<MediaStream | null>(null);
  const secondaryStream = useRef<MediaStream | null>(null);
  const primaryVideo = useRef<HTMLVideoElement | null>(null);
  const secondaryVideo = useRef<HTMLVideoElement | null>(null);

  const refresh = useCallback(async (signal?: AbortSignal) => {
    await Promise.resolve();
    try {
      const next = await fetchCandidateDashboard(signal);
      setDashboard(next);
      setStatus(next.assigned_examinations.length ? "Candidate workflow ready. Complete the prerequisites shown for the assigned examination." : "Candidate workflow resolved: no examination is currently assigned.");
      setError("");
    }
    catch (reason) { if (!(reason instanceof DOMException && reason.name === "AbortError")) setError(reason instanceof Error ? reason.message : "Unable to load candidate workflow."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const controller = new AbortController(); const task = window.setTimeout(() => void refresh(controller.signal), 0); return () => { window.clearTimeout(task); controller.abort(); }; }, [refresh]);
  useEffect(() => () => [...(primaryStream.current?.getTracks() ?? []), ...(secondaryStream.current?.getTracks() ?? [])].forEach((track) => track.stop()), []);

  async function acceptConsent() {
    if (!consentChecked) return;
    setBusy(true);
    try { await acceptCandidateConsent(); setActionStatus("Consent version CONSENT-1.0 recorded as a new immutable record."); await refresh(); }
    catch (reason) { setActionStatus(reason instanceof Error ? reason.message : "Consent could not be recorded."); }
    finally { setBusy(false); }
  }

  async function discoverDevices() {
    setBusy(true);
    setActionStatus("Releasing existing previews and requesting camera access...");
    try {
      stopMediaStream(primaryStream.current); stopMediaStream(secondaryStream.current);
      primaryStream.current = null; secondaryStream.current = null;
      if (primaryVideo.current) primaryVideo.current.srcObject = null;
      if (secondaryVideo.current) secondaryVideo.current.srcObject = null;
      const { devices: videoDevices, allDevices: devices } = await discoverVideoDevices();
      const details = browserDetails();
      const result = await submitDeviceCheck({ supported_browser: details.supported, secure_context: window.isSecureContext, camera_available: videoDevices.length > 0, microphone_available: devices.some((device) => device.kind === "audioinput"), browser_name: details.name, browser_version: details.version, operating_system: navigator.platform, user_agent: navigator.userAgent }) as { passed: boolean };
      setCameras(videoDevices);
      const recommendation = recommendCameraRoles(videoDevices, readCameraRoles());
      setPrimaryId(recommendation.primaryId);
      setSecondaryId(recommendation.secondaryId);
      setRolesConfirmed(false);
      setRoleReason(recommendation.reason);
      const discovery = videoDevices.length >= 2 ? `${videoDevices.length} cameras discovered. Review the assignments for Mode B, or preview the primary camera for Mode A/C.` : "One camera was discovered. Mode A/C can proceed; Mode B requires a distinct second camera.";
      setActionStatus(result.passed ? discovery : `${discovery} One or more browser-reported device checks failed.`);
      await refresh();
    } catch (reason) {
      await submitCameraPermission("primary", "denied").catch(() => undefined);
      setCameras([]); setPrimaryId(""); setSecondaryId(""); setRolesConfirmed(false);
      const failure = classifyMediaError(reason);
      setActionStatus(`Camera discovery failed (${failure.kind.replaceAll("_", " ")}): ${failure.message}`);
    } finally { setBusy(false); }
  }

  async function previewCamera(role: "primary" | "secondary") {
    if (role === "secondary" && !rolesConfirmed) { setStatus("Confirm the primary and secondary assignments before starting the secondary preview."); return; }
    const deviceId = role === "primary" ? primaryId : secondaryId;
    if (role === "secondary") {
      const pairError = validateCameraPair(primaryId, secondaryId);
      if (pairError) { setStatus(pairError); return; }
    }
    const device = cameras.find((item) => item.deviceId === deviceId);
    setBusy(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
      const streamRef = role === "primary" ? primaryStream : secondaryStream;
      const videoRef = role === "primary" ? primaryVideo : secondaryVideo;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      await submitCameraSelection({ camera_role: role, device_id: deviceId, label: device?.label || `${role} camera`, group_id: device?.groupId || null, camera_count: cameras.length, metadata: role === "primary" ? { preview_live_confirmed: true, mirror_assistance_confirmed: mirrorConfirmed } : { preview_live_confirmed: true } });
      await submitCameraPermission(role, "granted");
      setActionStatus(`${role === "primary" ? "Primary" : "Secondary"} camera preview is live.`);
      await refresh();
    } catch (reason) {
      await submitCameraPermission(role, "denied").catch(() => undefined);
      const failure = classifyMediaError(reason, "playback");
      setActionStatus(`${role === "primary" ? "Primary" : "Secondary"} camera preview failed (${failure.kind.replaceAll("_", " ")}): ${failure.message}`);
    } finally { setBusy(false); }
  }

  function confirmRoles() {
    const pairError = validateCameraPair(primaryId, secondaryId);
    if (pairError) { setStatus(pairError); return; }
    const primary = cameras.find((camera) => camera.deviceId === primaryId);
    const secondary = cameras.find((camera) => camera.deviceId === secondaryId);
    if (!primary || !secondary) { setStatus("Select two available cameras before confirming roles."); return; }
    persistCameraRoles({
      primaryId,
      secondaryId,
      primaryLabel: cameraLabel(primary, "Candidate-facing camera"),
      secondaryLabel: cameraLabel(secondary, "Environmental camera"),
      confirmedAt: new Date().toISOString(),
    });
    setRolesConfirmed(true);
    setRoleReason("Candidate confirmed these role assignments. The primary choice is also saved for facial enrolment and authentication.");
    setStatus(`Confirmed: primary ${cameraLabel(primary)}; secondary ${cameraLabel(secondary)}.`);
  }

  function swapRoles() {
    setPrimaryId(secondaryId);
    setSecondaryId(primaryId);
    setRolesConfirmed(false);
    setRoleReason("Roles were intentionally swapped. Review the labels and confirm the new assignments.");
    primaryStream.current?.getTracks().forEach((track) => track.stop());
    secondaryStream.current?.getTracks().forEach((track) => track.stop());
  }

  async function startExam(examinationId: string, mode: "A" | "B" | "C") {
    if (!primaryStream.current?.active) { setStatus("A live primary-camera preview is required before session start."); return; }
    if (mode === "B") {
      if (!rolesConfirmed) { setStatus("Confirm the displayed camera roles before starting a Mode B session."); return; }
      const pairError = validateCameraPair(primaryId, secondaryId);
      if (pairError) { setStatus(pairError); return; }
      if (!secondaryStream.current?.active) { setStatus("A live secondary-camera preview is required before a Mode B session starts."); return; }
    }
    if (mode === "C" && !mirrorConfirmed) { setStatus("Confirm the Mode C mirror-assisted arrangement before session start."); return; }
    setBusy(true);
    try {
      if (mode === "C") {
        const device = cameras.find((item) => item.deviceId === primaryId);
        await submitCameraSelection({ camera_role: "primary", device_id: primaryId, label: device?.label || "primary camera", group_id: device?.groupId || null, camera_count: cameras.length, metadata: { preview_live_confirmed: true, mirror_assistance_confirmed: true } });
      }
      const session = await startCandidateSession(examinationId, mode);
      primaryStream.current.getTracks().forEach((track) => track.stop());
      secondaryStream.current?.getTracks().forEach((track) => track.stop());
      router.push(`/candidate/examinations/${session.session_id}`);
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : "Examination could not start."); setBusy(false); }
  }

  if (loading) return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Preparing the candidate workflow."><LoadingState /></PortalShell>;
  if (error) return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Candidate workflow unavailable."><ErrorState message={error} onRetry={() => { setLoading(true); void refresh(); }} /></PortalShell>;

  return <PortalShell allowedRoles={["Candidate"]} title="Candidate Portal" badge="Candidate" summary="Complete consent and the camera setup required by the assigned monitoring mode before entering the bounded demonstration examination workspace.">
    <p className="workflow-status" role="status" aria-live="polite">{status}</p>
    {actionStatus && <p className="form-note" role="status" aria-live="polite">{actionStatus}</p>}
    {dashboard?.active_session && <section className="card active-session"><StatusBadge label="Active demonstration" tone="success" /><h2>Resume monitored workspace</h2><Link className="button-link" href={`/candidate/examinations/${dashboard.active_session.session_id}`}>Open demonstration workspace</Link></section>}
    <section className="status-grid">
      <article className="card"><span className="badge">Assigned examinations</span><h2>Available demonstrations</h2>{dashboard?.assigned_examinations.length ? dashboard.assigned_examinations.map((exam) => { const mode = exam.monitoring_mode as "A" | "B" | "C"; const readiness = dashboard.readiness_by_mode[mode] ?? {}; return <div className="assignment" key={exam.assignment_id}><strong>{exam.title}</strong><span>{exam.exam_code} · {exam.duration_minutes} minutes · Mode {mode}</span><button disabled={busy || !readiness.ready_to_start} onClick={() => void startExam(exam.examination_id, mode)}>Start demonstration</button></div>; }) : <p>No assigned examinations are available.</p>}</article>
      <article className="card"><span className="badge">Consent</span><h2>Required agreements</h2><label className="check-row"><input type="checkbox" checked={consentChecked} onChange={(event) => setConsentChecked(event.target.checked)} />I accept monitoring, the privacy notice, and institutional examination policy.</label><button disabled={busy || !consentChecked} onClick={() => void acceptConsent()}>Accept consent</button><p>{dashboard?.consent?.accepted ? `Accepted (${dashboard.consent.consent_version})` : "Valid consent required"}</p></article>
    </section>
    <section className="card camera-setup"><div className="section-heading"><div><span className="badge">Mode-aware camera setup</span><h2>Candidate-facing and environmental views</h2></div><button disabled={busy} onClick={() => void discoverDevices()}>Discover cameras and check device</button></div>{cameras.length === 1 && <div className="inline-warning" role="status">One camera supports Mode A and Mode C. Mode B requires a distinct second video-input device.</div>}<p className="camera-role-reason" role="status">{roleReason}</p><div className="camera-assignment-summary"><strong>Primary: {cameraLabel(cameras.find((camera) => camera.deviceId === primaryId))}</strong><strong>Secondary: {cameraLabel(cameras.find((camera) => camera.deviceId === secondaryId))}</strong><span>{rolesConfirmed ? "Assignments confirmed" : "Confirmation required"}</span></div><div className="camera-role-actions"><button type="button" disabled={!primaryId || !secondaryId} onClick={swapRoles}>Swap roles intentionally</button><button type="button" className="primary-action" disabled={!primaryId || !secondaryId || rolesConfirmed} onClick={confirmRoles}>{rolesConfirmed ? "Roles confirmed" : "Confirm camera roles"}</button></div><div className="dual-camera-grid">{(["primary", "secondary"] as const).map((role) => { const selected = role === "primary" ? primaryId : secondaryId; return <article className="camera-panel setup-panel" key={role}><h3>{role === "primary" ? "Primary camera" : "Secondary camera"}</h3><p>{role === "primary" ? "Candidate-facing view: face and upper body" : "Room, desk, side-angle or wider environmental view"}</p><select aria-label={`${role} camera device`} value={selected} onChange={(event) => { setRolesConfirmed(false); role === "primary" ? setPrimaryId(event.target.value) : setSecondaryId(event.target.value); }}><option value="">Select {role} camera</option>{cameras.map((camera) => <option value={camera.deviceId} key={camera.deviceId}>{camera.label || `Camera ${cameras.indexOf(camera) + 1}`}</option>)}</select><button disabled={busy || !selected || (role === "secondary" && !rolesConfirmed)} onClick={() => void previewCamera(role)}>Confirm and preview {role} camera</button><video ref={role === "primary" ? primaryVideo : secondaryVideo} autoPlay muted playsInline aria-label={`${role} camera local preview`} /></article>; })}</div><label className="check-row"><input type="checkbox" checked={mirrorConfirmed} onChange={(event) => setMirrorConfirmed(event.target.checked)} />For Mode C only, I confirm that the physical mirror-assisted arrangement is in place and the primary preview covers the intended view. SERPS records this attestation; it does not detect mirrors.</label><p className="privacy-note">Camera previews are local to this browser. SERPS persists operational metadata and EvidenceEvents, not raw video.</p></section>
    <section className="card readiness-card"><h2>Session readiness</h2><p>Device and permission values are client-reported browser attestations received by the server; they are evidence inputs, not independent hardware proof.</p><ReadinessSummary readiness={dashboard?.assigned_examinations[0] ? dashboard.readiness_by_mode[dashboard.assigned_examinations[0].monitoring_mode as "A" | "B" | "C"] ?? {} : {}} /></section>
  </PortalShell>;
}
