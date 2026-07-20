"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { ConfirmationDialog, ErrorState, LoadingState, StatusBadge } from "../../../../components/OperationalStates";
import { PortalShell } from "../../../../components/PortalShell";
import { completeCandidateSession, fetchCandidateWorkspace, submitEvidenceEvent } from "../../../../lib/api";
import type { CandidateWorkspace } from "../../../../lib/contracts";
import { formatElapsed } from "../../../../lib/operational";

const questions = [
  { prompt: "Which principle best describes SERPS decision authority?", options: ["Fully autonomous discipline", "Human-governed advisory support", "Automatic examination termination", "Unreviewed biometric scoring"] },
  { prompt: "What is the purpose of the secondary camera in this demonstration?", options: ["Question scoring", "Room or side-angle context", "Operating-system lockdown", "Candidate registration"] },
  { prompt: "Which record preserves a reviewer’s final operational action?", options: ["EvidenceEvent", "Device check", "ReviewerDecision", "Camera label"] },
];

function DemonstrationWorkspacePageContent() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [workspace, setWorkspace] = useState<CandidateWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Preparing monitored demonstration...");
  const [elapsed, setElapsed] = useState("00:00:00");
  const [question, setQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [finishOpen, setFinishOpen] = useState(false);
  const [finished, setFinished] = useState(false);
  const [faceCapability, setFaceCapability] = useState("Checking browser FaceDetector support...");
  const [primaryState, setPrimaryState] = useState("connecting");
  const [secondaryState, setSecondaryState] = useState("connecting");
  const primaryVideo = useRef<HTMLVideoElement | null>(null);
  const secondaryVideo = useRef<HTMLVideoElement | null>(null);
  const streams = useRef<MediaStream[]>([]);

  const stopMedia = useCallback(() => { streams.current.flatMap((stream) => stream.getTracks()).forEach((track) => track.stop()); streams.current = []; }, []);
  const emit = useCallback(async (eventType: string, description: string, cameraId?: "primary" | "secondary", confidence = 1) => {
    if (!workspace) return;
    await submitEvidenceEvent({ session_id: workspace.session.session_id, candidate_id: workspace.candidate.candidate_id, event_type: eventType, description, camera_id: cameraId, confidence });
  }, [workspace]);

  useEffect(() => { const controller = new AbortController(); fetchCandidateWorkspace(sessionId, controller.signal).then((result) => { setWorkspace(result); setStatus("Demonstration workspace active. This is not a secure browser or complete CBT platform."); }).catch((reason) => setError(reason instanceof Error ? reason.message : "Workspace could not load.")).finally(() => setLoading(false)); return () => controller.abort(); }, [sessionId]);
  useEffect(() => { if (!workspace) return; const tick = () => setElapsed(formatElapsed(workspace.session.started_at, Date.now())); tick(); const interval = window.setInterval(tick, 1000); return () => window.clearInterval(interval); }, [workspace]);

  useEffect(() => {
    if (!workspace || finished) return;
    let disposed = false;
    async function connect(role: "primary" | "secondary", deviceId: string, video: RefObject<HTMLVideoElement | null>) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
        if (disposed) { stream.getTracks().forEach((track) => track.stop()); return; }
        streams.current.push(stream);
        if (video.current) video.current.srcObject = stream;
        role === "primary" ? setPrimaryState("connected") : setSecondaryState("connected");
        await emit("CAMERA_CONNECTED", `${role} camera stream connected in the demonstration workspace.`, role);
        stream.getVideoTracks().forEach((track) => track.addEventListener("ended", () => {
          role === "primary" ? setPrimaryState("disconnected") : setSecondaryState("disconnected");
          void emit("CAMERA_DISCONNECTED", `${role} camera track ended or permission was revoked.`, role);
        }, { once: true }));
      } catch (reason) {
        role === "primary" ? setPrimaryState("permission denied") : setSecondaryState("permission denied");
        await emit("CAMERA_DISCONNECTED", `${role} camera could not connect: ${reason instanceof Error ? reason.message : "permission denied"}.`, role);
      }
    }
    void Promise.all([
      connect("primary", workspace.primary_camera.device_id, primaryVideo),
      connect("secondary", workspace.secondary_camera.device_id, secondaryVideo),
    ]).then(async () => {
      const DetectorConstructor = (window as unknown as { FaceDetector?: new () => { detect(source: HTMLVideoElement): Promise<unknown[]> } }).FaceDetector;
      if (!DetectorConstructor) { setFaceCapability("FaceDetector unavailable in this browser. Camera and tab monitoring remain active; no face result is fabricated."); return; }
      setFaceCapability("Browser FaceDetector available.");
      if (primaryVideo.current) {
        const faces = await new DetectorConstructor().detect(primaryVideo.current).catch(() => []);
        await emit(faces.length ? "FACE_DETECTED" : "FACE_NOT_DETECTED", faces.length ? "Browser FaceDetector detected a face in the primary view." : "Browser FaceDetector did not detect a face in the primary view.", "primary", 0.8);
      }
    });
    const visibility = () => { if (document.hidden) void emit("TAB_FOCUS_LOST", "Demonstration workspace lost document visibility."); };
    const deviceChange = async () => {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const ids = new Set(devices.filter((item) => item.kind === "videoinput").map((item) => item.deviceId));
      if (!ids.has(workspace.primary_camera.device_id)) { setPrimaryState("device removed"); void emit("CAMERA_DISCONNECTED", "Primary camera device was removed.", "primary"); }
      if (!ids.has(workspace.secondary_camera.device_id)) { setSecondaryState("device removed"); void emit("CAMERA_DISCONNECTED", "Secondary camera device was removed.", "secondary"); }
    };
    document.addEventListener("visibilitychange", visibility);
    navigator.mediaDevices?.addEventListener("devicechange", deviceChange);
    return () => { disposed = true; document.removeEventListener("visibilitychange", visibility); navigator.mediaDevices?.removeEventListener("devicechange", deviceChange); stopMedia(); };
  }, [workspace, finished, emit, stopMedia]);

  async function finish() {
    setFinishOpen(false);
    try { stopMedia(); await completeCandidateSession(sessionId); setFinished(true); setStatus("Demonstration completed. Evidence and governance records were preserved for review."); }
    catch (reason) { setStatus(reason instanceof Error ? reason.message : "The demonstration could not be completed."); }
  }

  if (loading) return <section className="workspace-shell"><LoadingState label="Loading authorised demonstration workspace..." /></section>;
  if (error || !workspace) return <section className="workspace-shell"><ErrorState message={error || "Workspace unavailable."} /></section>;
  return <section className="workspace-shell">
    <header className="workspace-header"><div><p className="eyebrow dark">Assessment Demonstration Harness</p><h1>{workspace.examination.title}</h1><p>{workspace.candidate.full_name} · {workspace.institution.name} · Session {workspace.session.session_id}</p></div><div className="timer" role="timer" aria-live="off"><span>Elapsed demonstration time</span><strong>{elapsed}</strong></div></header>
    <aside className="monitoring-notice" role="note"><strong>Monitoring notice:</strong> This bounded workspace generates real browser-originated EvidenceEvents. It does not provide operating-system lockdown, process blocking, clipboard enforcement, production scoring, or secure-browser guarantees.</aside>
    <p className="workflow-status" role="status" aria-live="polite">{status}</p>
    <section className="dual-camera-grid workspace-cameras"><article className="camera-panel"><div className="camera-title"><h2>Primary camera</h2><StatusBadge label={primaryState} tone={primaryState === "connected" ? "success" : "danger"} /></div><video ref={primaryVideo} autoPlay muted playsInline aria-label="Primary candidate-facing live local preview" /><p>Candidate-facing face and upper-body view.</p></article><article className="camera-panel"><div className="camera-title"><h2>Secondary camera</h2><StatusBadge label={secondaryState} tone={secondaryState === "connected" ? "success" : "danger"} /></div><video ref={secondaryVideo} autoPlay muted playsInline aria-label="Secondary room or side-angle live local preview" /><p>Room, desk or side-angle environmental view.</p></article></section>
    <div className="capability-disclosure"><strong>Face detection capability:</strong> {faceCapability}</div>
    <section className="question-workspace" aria-labelledby="question-title"><div className="question-progress">Question {question + 1} of {questions.length}</div><h2 id="question-title">{questions[question].prompt}</h2><fieldset><legend className="sr-only">Choose one answer</legend>{questions[question].options.map((option, index) => <label className="answer-option" key={option}><input type="radio" name={`question-${question}`} checked={answers[question] === index} onChange={() => setAnswers((current) => ({ ...current, [question]: index }))} />{option}</label>)}</fieldset><div className="question-actions"><button disabled={question === 0} onClick={() => setQuestion((value) => Math.max(0, value - 1))}>Previous</button><button disabled={question === questions.length - 1} onClick={() => setQuestion((value) => Math.min(questions.length - 1, value + 1))}>Next</button><button className="danger-action" disabled={finished} onClick={() => setFinishOpen(true)}>Finish demonstration</button></div></section>
    {finished && <section className="state-card" role="status"><StatusBadge label="Completed" tone="success" /><h2>Demonstration finished</h2><p>The session is now available in reviewer and administrator operational views.</p></section>}
    <ConfirmationDialog open={finishOpen} title="Finish this demonstration?" detail="This completes the session and stops both local camera tracks. Evidence and governance records remain append-only." confirmLabel="Finish demonstration" onConfirm={() => void finish()} onCancel={() => setFinishOpen(false)} />
  </section>;
}

export default function DemonstrationWorkspacePage() {
  return <PortalShell allowedRoles={["Candidate"]} title="Demonstration Examination Workspace" badge="Candidate" summary="A bounded monitored assessment harness; not a complete CBT platform or secure browser."><DemonstrationWorkspacePageContent /></PortalShell>;
}
