"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { ConfirmationDialog, ErrorState, LoadingState, StatusBadge } from "../../../../components/OperationalStates";
import { PortalShell } from "../../../../components/PortalShell";
import { beginPeriodicVerification, completeCandidateSession, fetchCandidateWorkspace, fetchIdentityStatus, submitEvidenceEvent } from "../../../../lib/api";
import { AUDIO_MONITOR_NAME, AUDIO_MONITOR_VERSION, AUDIO_SAMPLE_INTERVAL_MS, AudioActivityTracker, LocalAudioMonitor } from "../../../../lib/audioMonitoring";
import type { CandidateWorkspace } from "../../../../lib/contracts";
import { audioEvidence, detectorUnavailableEvidence, DuplicateEventGate, objectEvidence, objectRolesForMode, type CameraRole, type EvidenceDraft } from "../../../../lib/multimodalEvents";
import { LocalObjectDetector, OBJECT_MODEL_NAME, OBJECT_MODEL_VERSION, OBJECT_SAMPLE_INTERVAL_MS } from "../../../../lib/objectDetection";
import { formatElapsed } from "../../../../lib/operational";

const questions = [
  { prompt: "Which principle best describes SERPS decision authority?", options: ["Fully autonomous discipline", "Human-governed advisory support", "Automatic examination termination", "Unreviewed biometric scoring"] },
  { prompt: "What is the purpose of the secondary camera in this demonstration?", options: ["Question scoring", "Room or side-angle context", "Operating-system lockdown", "Candidate registration"] },
  { prompt: "Which record preserves a reviewer’s final operational action?", options: ["EvidenceEvent", "Device check", "ReviewerDecision", "Camera label"] },
];

const modeDescription = {
  A: "Mode A: object inference uses the primary candidate-facing camera only; no secondary-camera corroboration is expected.",
  B: "Mode B: object inference samples both primary and environmental cameras; audio is acquired once from the selected browser microphone.",
  C: "Mode C: object inference uses the primary camera only. Mirror assistance adds viewing context but does not create an independent evidence source.",
};

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
  const [objectStates, setObjectStates] = useState<Record<CameraRole, string>>({ primary: "loading", secondary: "loading" });
  const [objectSummary, setObjectSummary] = useState<Record<CameraRole, string>>({ primary: "No sample yet", secondary: "No sample yet" });
  const [audioState, setAudioState] = useState("requesting permission");
  const [audioLevel, setAudioLevel] = useState(0);
  const [periodicDue, setPeriodicDue] = useState(false);
  const [lastHeartbeat, setLastHeartbeat] = useState<string | null>(null);

  const primaryVideo = useRef<HTMLVideoElement | null>(null);
  const secondaryVideo = useRef<HTMLVideoElement | null>(null);
  const streams = useRef<MediaStream[]>([]);
  const streamByRole = useRef<Partial<Record<CameraRole, MediaStream>>>({});
  const disconnectReported = useRef(new Set<string>());
  const objectDetectors = useRef<Partial<Record<CameraRole, LocalObjectDetector>>>({});
  const audioMonitor = useRef<LocalAudioMonitor | null>(null);

  const stopMedia = useCallback(async () => {
    streams.current.flatMap((stream) => stream.getTracks()).forEach((track) => track.stop());
    streams.current = [];
    streamByRole.current = {};
    Object.values(objectDetectors.current).forEach((detector) => detector?.close());
    objectDetectors.current = {};
    await audioMonitor.current?.close();
    audioMonitor.current = null;
  }, []);

  const emit = useCallback(async (
    eventType: string,
    description: string,
    cameraId?: CameraRole,
    confidence = 1,
    riskWeight?: number,
    metadata: Record<string, unknown> = {},
  ) => {
    if (!workspace) return;
    await submitEvidenceEvent({
      session_id: workspace.session.session_id,
      candidate_id: workspace.candidate.candidate_id,
      event_type: eventType,
      description,
      camera_id: cameraId,
      confidence,
      risk_weight: riskWeight,
      metadata_json: { ...metadata, correlation_window_seconds: metadata.correlation_window_seconds ?? 60 },
    });
  }, [workspace]);

  const emitDraft = useCallback(async (draft: EvidenceDraft) => {
    await emit(draft.eventType, draft.description, draft.cameraId, draft.confidence, draft.riskWeight, draft.metadata);
  }, [emit]);

  useEffect(() => {
    const controller = new AbortController();
    fetchCandidateWorkspace(sessionId, controller.signal)
      .then((result) => {
        setWorkspace(result);
        setStatus("Demonstration workspace active. This is not a secure browser or complete CBT platform.");
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Workspace could not load."))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [sessionId]);

  useEffect(() => {
    if (!workspace) return;
    const tick = () => setElapsed(formatElapsed(workspace.session.started_at, Date.now()));
    tick();
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [workspace]);

  useEffect(() => {
    if (!workspace) return;
    let timer = 0;
    void fetchIdentityStatus().then((identity) => {
      if (identity.biometric_required && !identity.demo_bypass) timer = window.setTimeout(() => setPeriodicDue(true), 120000);
    }).catch(() => undefined);
    return () => window.clearTimeout(timer);
  }, [workspace]);

  useEffect(() => {
    if (!workspace || finished) return;
    let disposed = false;
    const timers: number[] = [];
    const objectGate = new DuplicateEventGate(12000);
    const audioTracker = new AudioActivityTracker();
    let audioDisconnectReported = false;

    async function connect(role: CameraRole, deviceId: string, video: RefObject<HTMLVideoElement | null>, reconnected = false) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
        if (disposed) { stream.getTracks().forEach((track) => track.stop()); return; }
        streams.current.push(stream);
        streamByRole.current[role]?.getTracks().forEach((track) => track.stop());
        streamByRole.current[role] = stream;
        disconnectReported.current.delete(role);
        if (video.current) {
          video.current.srcObject = stream;
          await video.current.play().catch(() => undefined);
        }
        role === "primary" ? setPrimaryState("connected") : setSecondaryState("connected");
        await emit(reconnected ? "camera_reconnected" : "camera_connected", `${role} camera stream ${reconnected ? "reconnected and revalidated" : "connected"} in the demonstration workspace.`, role);
        stream.getVideoTracks().forEach((track) => {
          const disconnected = (reason: string) => {
            if (disconnectReported.current.has(role)) return;
            disconnectReported.current.add(role);
            streamByRole.current[role] = undefined;
            if (video.current) video.current.srcObject = null;
            role === "primary" ? setPrimaryState("disconnected") : setSecondaryState("disconnected");
            void emit("camera_disconnected", `${role} camera ${reason}.`, role);
          };
          track.addEventListener("ended", () => disconnected("track ended or permission was revoked"), { once: true });
          track.addEventListener("mute", () => disconnected("stream became unavailable"), { once: true });
        });
      } catch (reason) {
        role === "primary" ? setPrimaryState("permission denied") : setSecondaryState("permission denied");
        await emit("camera_disconnected", `${role} camera could not connect: ${reason instanceof Error ? reason.message : "permission denied"}.`, role);
      }
    }

    async function startObjectDetector(role: CameraRole, video: RefObject<HTMLVideoElement | null>) {
      try {
        setObjectStates((current) => ({ ...current, [role]: "loading model" }));
        const detector = new LocalObjectDetector();
        await detector.initialise();
        if (disposed) { detector.close(); return; }
        objectDetectors.current[role] = detector;
        setObjectStates((current) => ({ ...current, [role]: "ready" }));
        const timer = window.setInterval(() => {
          if (disposed || !video.current || video.current.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
          try {
            const snapshot = detector.detect(video.current);
            setObjectSummary((current) => ({ ...current, [role]: `${snapshot.personCount} person(s), ${snapshot.mobilePhoneCount} phone(s); ${snapshot.processingTime.toFixed(0)} ms` }));
            for (const draft of objectEvidence(snapshot, role)) {
              if (objectGate.allow(`${draft.eventType}:${role}`, Date.now())) void emitDraft(draft);
            }
          } catch (reason) {
            const message = reason instanceof Error ? reason.message : "inference failed";
            setObjectStates((current) => ({ ...current, [role]: "unavailable" }));
            if (objectGate.allow(`object_detector_unavailable:${role}`, Date.now())) void emitDraft(detectorUnavailableEvidence(role, message));
          }
        }, OBJECT_SAMPLE_INTERVAL_MS);
        timers.push(timer);
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : "model loading failed";
        setObjectStates((current) => ({ ...current, [role]: "unavailable" }));
        if (objectGate.allow(`object_detector_unavailable:${role}`, Date.now())) await emitDraft(detectorUnavailableEvidence(role, message));
      }
    }

    async function startAudioMonitor() {
      try {
        const monitor = new LocalAudioMonitor();
        audioMonitor.current = monitor;
        const stream = await monitor.start();
        if (disposed) { await monitor.close(); return; }
        setAudioState("active");
        await emit("microphone_connected", "The candidate microphone audio track connected to the local privacy-safe activity monitor.", undefined, 1, 0, {
          source: "local_browser_audio_monitor",
          detector_name: AUDIO_MONITOR_NAME,
          detector_version: AUDIO_MONITOR_VERSION,
          threshold: audioTracker.threshold,
          raw_audio_stored: false,
        });
        const disconnected = (reason: string) => {
          if (audioDisconnectReported) return;
          audioDisconnectReported = true;
          setAudioState("disconnected");
          void emit("microphone_disconnected", `The candidate microphone ${reason}.`, undefined, 1, 0.1, {
            source: "local_browser_audio_monitor",
            detector_version: AUDIO_MONITOR_VERSION,
            raw_audio_stored: false,
          });
        };
        stream.getAudioTracks().forEach((track) => {
          track.addEventListener("ended", () => disconnected("track ended or permission was revoked"), { once: true });
          track.addEventListener("mute", () => disconnected("became unavailable"), { once: true });
        });
        const timer = window.setInterval(() => {
          if (disposed) return;
          try {
            const level = monitor.sampleLevel();
            setAudioLevel(level);
            for (const signal of audioTracker.update(level, performance.now())) void emitDraft(audioEvidence(signal));
          } catch (reason) {
            setAudioState("unavailable");
            if (!audioDisconnectReported) {
              audioDisconnectReported = true;
              void emit("audio_monitor_unavailable", `The local audio monitor became unavailable: ${reason instanceof Error ? reason.message : "analysis failed"}.`, undefined, 1, 0, {
                source: "local_browser_audio_monitor",
                detector_version: AUDIO_MONITOR_VERSION,
                raw_audio_stored: false,
              });
            }
          }
        }, AUDIO_SAMPLE_INTERVAL_MS);
        timers.push(timer);
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : "microphone permission or Web Audio support unavailable";
        setAudioState("unavailable");
        await emit("audio_monitor_unavailable", `The local audio monitor could not start: ${message}.`, undefined, 1, 0, {
          source: "local_browser_audio_monitor",
          detector_name: AUDIO_MONITOR_NAME,
          detector_version: AUDIO_MONITOR_VERSION,
          unavailable_reason: message,
          raw_audio_stored: false,
        });
      }
    }

    const activeObjectRoles = objectRolesForMode(workspace.session.deployment_mode);
    const secondaryUsed = activeObjectRoles.includes("secondary");
    const cameraStarts = [connect("primary", workspace.primary_camera.device_id, primaryVideo)];
    if (secondaryUsed) cameraStarts.push(connect("secondary", workspace.secondary_camera.device_id, secondaryVideo));
    void Promise.all(cameraStarts).then(async () => {
      if (disposed) return;
      await startObjectDetector("primary", primaryVideo);
      if (secondaryUsed) await startObjectDetector("secondary", secondaryVideo);
      const DetectorConstructor = (window as unknown as { FaceDetector?: new () => { detect(source: HTMLVideoElement): Promise<unknown[]> } }).FaceDetector;
      if (!DetectorConstructor) {
        setFaceCapability("Browser FaceDetector unavailable. Identity assurance remains available through the separate locally bundled MediaPipe enrolment/authentication workflow; no face result is fabricated here.");
      } else if (primaryVideo.current) {
        setFaceCapability("Browser FaceDetector available for bounded session-state evidence.");
        const faces = await new DetectorConstructor().detect(primaryVideo.current).catch(() => []);
        await emit(faces.length ? "face_detected" : "face_not_detected", faces.length ? "Browser FaceDetector detected a face in the primary view." : "Browser FaceDetector did not detect a face in the primary view.", "primary", 0.8);
      }
    });
    void startAudioMonitor();

    const visibility = () => { if (document.hidden) void emit("tab_focus_lost", "Demonstration workspace lost document visibility."); };
    const deviceChange = async () => {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const ids = new Set(devices.filter((item) => item.kind === "videoinput").map((item) => item.deviceId));
      if (!ids.has(workspace.primary_camera.device_id)) {
        if (!disconnectReported.current.has("primary")) {
          disconnectReported.current.add("primary");
          setPrimaryState("device removed");
          streamByRole.current.primary?.getTracks().forEach((track) => track.stop());
          streamByRole.current.primary = undefined;
          void emit("camera_disconnected", "Primary camera device was removed.", "primary");
        }
      } else if (!streamByRole.current.primary?.active) void connect("primary", workspace.primary_camera.device_id, primaryVideo, true);
      if (secondaryUsed) {
        if (!ids.has(workspace.secondary_camera.device_id)) {
          if (!disconnectReported.current.has("secondary")) {
            disconnectReported.current.add("secondary");
            setSecondaryState("device removed");
            streamByRole.current.secondary?.getTracks().forEach((track) => track.stop());
            streamByRole.current.secondary = undefined;
            void emit("camera_disconnected", "Secondary camera device was removed.", "secondary");
          }
        } else if (!streamByRole.current.secondary?.active) void connect("secondary", workspace.secondary_camera.device_id, secondaryVideo, true);
      }
    };
    document.addEventListener("visibilitychange", visibility);
    navigator.mediaDevices?.addEventListener("devicechange", deviceChange);
    const heartbeat = window.setInterval(() => {
      for (const role of (secondaryUsed ? ["primary", "secondary"] : ["primary"]) as CameraRole[]) {
        if (streamByRole.current[role]?.getVideoTracks().some((track) => track.readyState === "live" && !track.muted)) {
          void emit("camera_heartbeat", `${role} camera browser heartbeat.`, role);
        }
      }
      setLastHeartbeat(new Date().toISOString());
    }, 15000);
    timers.push(heartbeat);

    return () => {
      disposed = true;
      timers.forEach((timer) => window.clearInterval(timer));
      document.removeEventListener("visibilitychange", visibility);
      navigator.mediaDevices?.removeEventListener("devicechange", deviceChange);
      void stopMedia();
    };
  }, [workspace, finished, emit, emitDraft, stopMedia]);

  async function finish() {
    setFinishOpen(false);
    try {
      await stopMedia();
      await completeCandidateSession(sessionId);
      setFinished(true);
      setStatus("Demonstration completed. Evidence and governance records were preserved for review.");
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "The demonstration could not be completed.");
    }
  }

  async function beginPeriodic() {
    try {
      const challenge = await beginPeriodicVerification();
      sessionStorage.setItem("serps_face_challenge", challenge.challenge_token);
      sessionStorage.setItem("serps_face_actions", JSON.stringify(challenge.required_actions));
      sessionStorage.setItem("serps_face_mode", "periodic");
      sessionStorage.setItem("serps_face_return", window.location.pathname);
      await stopMedia();
      window.location.href = "/facial-auth";
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "Periodic identity verification could not begin.");
    }
  }

  if (loading) return <section className="workspace-shell"><LoadingState label="Loading authorised demonstration workspace..." /></section>;
  if (error || !workspace) return <section className="workspace-shell"><ErrorState message={error || "Workspace unavailable."} /></section>;

  return <section className="workspace-shell">
    <header className="workspace-header">
      <div><p className="eyebrow dark">Assessment Demonstration Harness</p><h1>{workspace.examination.title}</h1><p>{workspace.candidate.full_name} · {workspace.institution.name} · Session {workspace.session.session_id}</p></div>
      <div className="timer" role="timer" aria-live="off"><span>Elapsed demonstration time</span><strong>{elapsed}</strong></div>
    </header>
    <aside className="monitoring-notice" role="note"><strong>Monitoring notice:</strong> SERPS performs bounded local object and sound-activity analysis. Raw audio and raw video are not stored by default. Evidence informs human review and never determines misconduct or terminates an examination.</aside>
    <p className="workflow-status" role="status" aria-live="polite">{status}</p>
    <p className="freshness-note">Candidate device heartbeat: {lastHeartbeat ? new Date(lastHeartbeat).toLocaleTimeString() : "awaiting first update"}</p>
    <p className="mode-disclosure"><strong>Proctoring mode:</strong> {modeDescription[workspace.session.deployment_mode]}</p>
    {periodicDue && <aside className="identity-prompt" role="alert"><div><strong>Periodic identity verification due</strong><p>Pause the demonstration and complete a bounded facial/liveness check before continuing.</p></div><button className="primary-action" onClick={() => void beginPeriodic()}>Verify identity</button></aside>}

    <section className="dual-camera-grid workspace-cameras">
      <article className="camera-panel"><div className="camera-title"><h2>Primary camera</h2><StatusBadge label={primaryState} tone={primaryState === "connected" ? "success" : "danger"} /></div><video ref={primaryVideo} autoPlay muted playsInline aria-label="Primary candidate-facing live local preview" /><p>Candidate-facing face and upper-body view.</p><div className="detector-readout"><strong>Object detector: {objectStates.primary}</strong><span>{objectSummary.primary}</span></div></article>
      <article className="camera-panel"><div className="camera-title"><h2>Secondary camera</h2><StatusBadge label={workspace.session.deployment_mode === "B" ? secondaryState : `not used in Mode ${workspace.session.deployment_mode}`} tone={secondaryState === "connected" && workspace.session.deployment_mode === "B" ? "success" : "warning"} /></div><video ref={secondaryVideo} autoPlay muted playsInline aria-label="Secondary room or side-angle live local preview" /><p>Room, desk or side-angle environmental view.</p><div className="detector-readout"><strong>Object detector: {workspace.session.deployment_mode === "B" ? objectStates.secondary : "not used"}</strong><span>{workspace.session.deployment_mode === "B" ? objectSummary.secondary : "No independent secondary evidence expected"}</span></div></article>
    </section>

    <section className="multimodal-status-grid" aria-label="Multimodal detector status">
      <article className="card"><span className="badge">Local object intelligence</span><h2>{OBJECT_MODEL_NAME}</h2><p>Model version {OBJECT_MODEL_VERSION}; sampled every {OBJECT_SAMPLE_INTERVAL_MS / 1000} seconds for person and mobile-phone classes only.</p></article>
      <article className="card"><span className="badge">Privacy-safe audio activity</span><h2>Microphone: {audioState}</h2><p>{AUDIO_MONITOR_NAME} {AUDIO_MONITOR_VERSION}; current normalised RMS level {audioLevel.toFixed(4)}. No recording or transcription is performed.</p></article>
    </section>
    <div className="capability-disclosure"><strong>Face detection capability:</strong> {faceCapability}</div>
    <aside className="metadata-only-notice"><strong>Reviewer boundary:</strong> reviewer and administrator portals receive structured event metadata, CIE explanations and policy outcomes—not remote live media feeds.</aside>

    <section className="question-workspace" aria-labelledby="question-title">
      <div className="question-progress">Question {question + 1} of {questions.length}</div>
      <h2 id="question-title">{questions[question].prompt}</h2>
      <fieldset><legend className="sr-only">Choose one answer</legend>{questions[question].options.map((option, index) => <label className="answer-option" key={option}><input type="radio" name={`question-${question}`} checked={answers[question] === index} onChange={() => setAnswers((current) => ({ ...current, [question]: index }))} />{option}</label>)}</fieldset>
      <div className="question-actions"><button disabled={question === 0} onClick={() => setQuestion((value) => Math.max(0, value - 1))}>Previous</button><button disabled={question === questions.length - 1} onClick={() => setQuestion((value) => Math.min(questions.length - 1, value + 1))}>Next</button><button className="danger-action" disabled={finished} onClick={() => setFinishOpen(true)}>Finish demonstration</button></div>
    </section>
    {finished && <section className="state-card" role="status"><StatusBadge label="Completed" tone="success" /><h2>Demonstration finished</h2><p>The session is now available in reviewer and administrator operational views.</p></section>}
    <ConfirmationDialog open={finishOpen} title="Finish this demonstration?" detail="This completes the session and stops camera, object-detector and microphone resources. Evidence and governance records remain append-only." confirmLabel="Finish demonstration" onConfirm={() => void finish()} onCancel={() => setFinishOpen(false)} />
  </section>;
}

export default function DemonstrationWorkspacePage() {
  return <PortalShell allowedRoles={["Candidate"]} title="Demonstration Examination Workspace" badge="Candidate" summary="A bounded monitored assessment harness; not a complete CBT platform or secure browser."><DemonstrationWorkspacePageContent /></PortalShell>;
}
