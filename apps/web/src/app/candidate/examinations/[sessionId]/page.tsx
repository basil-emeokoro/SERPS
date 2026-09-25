"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { ConfirmationDialog, ErrorState, LoadingState, StatusBadge } from "../../../../components/OperationalStates";
import { PortalShell } from "../../../../components/PortalShell";
import { completeCandidateSession, fetchCandidateProtection, fetchCandidateWorkspace, submitEvidenceEvent, updateDemoPhonePolicy } from "../../../../lib/api";
import { AUDIO_MONITOR_NAME, AUDIO_MONITOR_VERSION, AUDIO_SAMPLE_INTERVAL_MS, AudioActivityTracker, LocalAudioMonitor } from "../../../../lib/audioMonitoring";
import type { CandidateWorkspace } from "../../../../lib/contracts";
import { audioEvidence, detectorUnavailableEvidence, DuplicateEventGate, faceDetectorUnavailableEvidence, facePresenceEvidence, objectEvidence, objectRolesForMode, type CameraRole, type EvidenceDraft } from "../../../../lib/multimodalEvents";
import { FACE_SAMPLE_INTERVAL_MS, FacePresenceTracker, LocalFacePerceptionService } from "../../../../lib/faceDetection";
import { LocalObjectDetector, OBJECT_MODEL_NAME, OBJECT_MODEL_VERSION, OBJECT_SAMPLE_INTERVAL_MS } from "../../../../lib/objectDetection";
import { formatElapsed } from "../../../../lib/operational";
import { activeElapsedMs, canDemoRestore, clearProtection, enterProtection, formatActiveElapsed, interactionDisabled, interruptionDurationMs, monitoringProtectionRequired, normalProtectionState, type ProtectionReason, type ProtectionState } from "../../../../lib/protectionState";

import FacialVerification from "../../../../components/FacialVerification";
import { fetchReauthentication, reauthenticationMessage, type ReauthenticationState } from "../../../../lib/reauthentication";

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
  const [faceCapability, setFaceCapability] = useState("Face monitoring: Loading local MediaPipe detector...");
  const [primaryState, setPrimaryState] = useState("connecting");
  const [secondaryState, setSecondaryState] = useState("connecting");
  const [objectStates, setObjectStates] = useState<Record<CameraRole, string>>({ primary: "loading", secondary: "loading" });
  const [objectSummary, setObjectSummary] = useState<Record<CameraRole, string>>({ primary: "No sample yet", secondary: "No sample yet" });
  const [audioState, setAudioState] = useState("requesting permission");
  const [audioLevel, setAudioLevel] = useState(0);
  const [identityRequirement, setIdentityRequirement] = useState<ReauthenticationState | null>(null);
  const [identityCheckOpen, setIdentityCheckOpen] = useState(false);
  const [lastHeartbeat, setLastHeartbeat] = useState<string | null>(null);
  const [protection, setProtection] = useState<ProtectionState>(() => normalProtectionState());
  const [demoControlsEnabled, setDemoControlsEnabled] = useState(false);
  const [demoPhonePolicyArmed, setDemoPhonePolicyArmed] = useState(false);

  const primaryVideo = useRef<HTMLVideoElement | null>(null);
  const secondaryVideo = useRef<HTMLVideoElement | null>(null);
  const streams = useRef<MediaStream[]>([]);
  const streamByRole = useRef<Partial<Record<CameraRole, MediaStream>>>({});
  const disconnectReported = useRef(new Set<string>());
  const connectionInFlight = useRef(new Set<CameraRole>());
  const objectDetectors = useRef<Partial<Record<CameraRole, LocalObjectDetector>>>({});
  const faceDetector = useRef<LocalFacePerceptionService | null>(null);
  const audioMonitor = useRef<LocalAudioMonitor | null>(null);
  const protectionRef = useRef(protection);
  const interruptionStartedAt = useRef<number | null>(null);
  const lastServerAckAt = useRef<number | null>(null);
  const connectivityFailures = useRef(0);
  const requiredMonitoringUnavailable = !!workspace && !finished && (
    primaryState !== "connected"
    || (workspace.session.deployment_mode === "B" && secondaryState !== "connected")
    || audioState !== "active"
    || !faceCapability.startsWith("Face monitoring: Active")
  );
  const monitoringProtectionActive = monitoringProtectionRequired(demoPhonePolicyArmed, requiredMonitoringUnavailable);

  useEffect(() => { protectionRef.current = protection; }, [protection]);
  useEffect(() => {
    if (protection.mode !== "PROTECTED") return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [protection.mode]);

  const stopMedia = useCallback(async () => {
    streams.current.flatMap((stream) => stream.getTracks()).forEach((track) => track.stop());
    streams.current = [];
    streamByRole.current = {};
    Object.values(objectDetectors.current).forEach((detector) => detector?.close());
    objectDetectors.current = {};
    faceDetector.current?.close();
    faceDetector.current = null;
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
        if (result.session.status === "completed") {
          setFinished(true);
          setElapsed(formatElapsed(result.session.started_at, result.session.ended_at ?? Date.now()));
          setStatus("Demonstration completed. Evidence and governance records were preserved for review.");
        } else {
          setStatus("Demonstration workspace active. This is not a secure browser or complete CBT platform.");
        }
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Workspace could not load."))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [sessionId]);

  useEffect(() => {
    if (!workspace || finished) return;
    const tick = () => setElapsed(formatActiveElapsed(activeElapsedMs(workspace.session.started_at, Date.now(), protectionRef.current)));
    tick();
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [workspace, finished]);

  const enterProtectedState = useCallback((reason: ProtectionReason, metadata: Record<string, unknown> = {}) => {
    const previous = protectionRef.current;
    const next = enterProtection(previous, reason, Date.now());
    if (next === previous) return;
    protectionRef.current = next;
    setProtection(next);
    void emit("protection_entered", "Examination content entered a governed protective pause.", undefined, 1, 0,
      { trigger_category: reason, protection_state: "PROTECTED", misconduct_determination: false, ...metadata });
  }, [emit]);

  const clearProtectedState = useCallback((expectedReason: ProtectionReason, metadata: Record<string, unknown> = {}, policyRecoveryConfirmed = false) => {
    const previous = protectionRef.current;
    if (previous.reason !== expectedReason) return;
    const next = clearProtection(previous, Date.now(), policyRecoveryConfirmed);
    if (next === previous) return;
    protectionRef.current = next;
    setProtection(next);
    void emit("protection_cleared", "Examination content protection cleared after readiness revalidation.", undefined, 1, 0,
      { trigger_category: expectedReason, protection_state: "NORMAL", misconduct_determination: false, ...metadata });
  }, [emit]);

  const refreshIdentityRequirement = useCallback(async () => {
    const next = await fetchReauthentication(sessionId);
    setIdentityRequirement(next);
    if (!next.required) setIdentityCheckOpen(false);
  }, [sessionId]);

  useEffect(() => {
    if (!workspace || finished) return;
    let disposed = false;
    const controller = new AbortController();
    const check = async () => {
      try {
        const next = await fetchReauthentication(sessionId, controller.signal);
        if (!disposed) { setIdentityRequirement(next); if (!next.required) setIdentityCheckOpen(false); }
      } catch { /* A read failure must never clear an existing requirement. */ }
    };
    void check();
    const interval = window.setInterval(() => void check(), 3000);
    return () => { disposed = true; controller.abort(); window.clearInterval(interval); };
  }, [workspace, finished, sessionId]);

  useEffect(() => {
    if (!workspace || finished) return;
    let disposed = false;
    const timers: number[] = [];
    const objectGate = new DuplicateEventGate(12000);
    const audioTracker = new AudioActivityTracker();
    let audioDisconnectReported = false;

    async function connect(role: CameraRole, deviceId: string, video: RefObject<HTMLVideoElement | null>, reconnected = false) {
      if (connectionInFlight.current.has(role)) return;
      connectionInFlight.current.add(role);
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
        await emit(
          reconnected ? "camera_reconnected" : "camera_connected",
          `${role} camera stream ${reconnected ? "reconnected and revalidated" : "connected"} in the demonstration workspace.`,
          role,
          1,
          0,
        );
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
      } finally {
        connectionInFlight.current.delete(role);
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

    async function startFaceMonitor() {
      const tracker = new FacePresenceTracker();
      try {
        const detector = new LocalFacePerceptionService();
        await detector.initialise();
        if (disposed) { detector.close(); return; }
        faceDetector.current = detector;
        setFaceCapability("Face monitoring: Active — Local MediaPipe detector");
        const timer = window.setInterval(() => {
          const stream = streamByRole.current.primary;
          const cameraConnected = !!stream?.active && stream.getVideoTracks().some((track) => track.readyState === "live" && !track.muted);
          if (disposed || !cameraConnected || !primaryVideo.current || primaryVideo.current.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
            tracker.update(0, performance.now(), false);
            return;
          }
          try {
            const snapshot = detector.detect(primaryVideo.current);
            for (const signal of tracker.update(snapshot.faceCount, performance.now(), true)) void emitDraft(facePresenceEvidence(signal, snapshot));
          } catch (reason) {
            const message = reason instanceof Error ? reason.message : "face inference failed";
            setFaceCapability(`Face monitoring: Degraded — Local MediaPipe detector unavailable (${message}). Other evidence sources remain active.`);
            if (objectGate.allow("face_detector_unavailable:primary", Date.now())) void emitDraft(faceDetectorUnavailableEvidence(message));
          }
        }, FACE_SAMPLE_INTERVAL_MS);
        timers.push(timer);
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : "model or WASM loading failed";
        setFaceCapability(`Face monitoring: Degraded — Local MediaPipe detector unavailable (${message}). Other evidence sources remain active.`);
        if (objectGate.allow("face_detector_unavailable:primary", Date.now())) await emitDraft(faceDetectorUnavailableEvidence(message));
      }
    }

    const activeObjectRoles = objectRolesForMode(workspace.session.deployment_mode);
    const secondaryUsed = activeObjectRoles.includes("secondary");
    const secondaryCamera = workspace.secondary_camera;
    if (secondaryUsed && !secondaryCamera) {
      const invalidModeTimer = window.setTimeout(() => setStatus("Mode B requires a configured secondary camera. Monitoring did not start."), 0);
      return () => { disposed = true; window.clearTimeout(invalidModeTimer); };
    }
    const cameraStarts = [connect("primary", workspace.primary_camera.device_id, primaryVideo)];
    if (secondaryUsed && secondaryCamera) cameraStarts.push(connect("secondary", secondaryCamera.device_id, secondaryVideo));
    void Promise.all(cameraStarts).then(async () => {
      if (disposed) return;
      await startObjectDetector("primary", primaryVideo);
      if (secondaryUsed) await startObjectDetector("secondary", secondaryVideo);
      await startFaceMonitor();
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
      } else if (disconnectReported.current.has("primary") || !streamByRole.current.primary?.active) {
        void connect("primary", workspace.primary_camera.device_id, primaryVideo, true);
      }
      if (secondaryUsed && secondaryCamera) {
        if (!ids.has(secondaryCamera.device_id)) {
          if (!disconnectReported.current.has("secondary")) {
            disconnectReported.current.add("secondary");
            setSecondaryState("device removed");
            streamByRole.current.secondary?.getTracks().forEach((track) => track.stop());
            streamByRole.current.secondary = undefined;
            void emit("camera_disconnected", "Secondary camera device was removed.", "secondary");
          }
        } else if (disconnectReported.current.has("secondary") || !streamByRole.current.secondary?.active) {
          void connect("secondary", secondaryCamera.device_id, secondaryVideo, true);
        }
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

  useEffect(() => {
    if (!workspace || finished) return;
    if (!monitoringProtectionActive) {
      clearProtectedState("monitoring_verification", {
        readiness_revalidated: !requiredMonitoringUnavailable,
        demo_phone_policy_armed: demoPhonePolicyArmed,
      });
      return;
    }
    const grace = window.setTimeout(() => enterProtectedState("monitoring_verification", {
      operational_integrity_condition: true,
      grace_period_ms: 5000,
      configured_mode: workspace.session.deployment_mode,
    }), 5000);
    return () => window.clearTimeout(grace);
  }, [workspace, finished, requiredMonitoringUnavailable, monitoringProtectionActive, demoPhonePolicyArmed, enterProtectedState, clearProtectedState]);

  useEffect(() => {
    if (!workspace || finished) return;
    let disposed = false;
    const checkServer = async () => {
      try {
        const policy = await fetchCandidateProtection(workspace.session.session_id);
        if (disposed) return;
        const now = Date.now();
        const priorInterruption = interruptionStartedAt.current;
        const priorAck = lastServerAckAt.current;
        connectivityFailures.current = 0;
        lastServerAckAt.current = now;
        setLastHeartbeat(new Date(now).toISOString());
        if (policy.state === "PROTECTED" && policy.policy_action === "PROTECT_AND_PAUSE") {
          enterProtectedState("policy_review", { policy_action: policy.policy_action, requires_reviewer: policy.requires_reviewer });
        } else if (protectionRef.current.reason === "policy_review") {
          clearProtectedState("policy_review", { reviewer_recovery_confirmed: true }, true);
        }
        setDemoControlsEnabled(policy.demo_controls_enabled);
        setDemoPhonePolicyArmed(policy.demo_phone_policy_armed);
        if (priorInterruption != null) {
          const duration = interruptionDurationMs(priorInterruption, now);
          interruptionStartedAt.current = null;
          await emit("connectivity_interrupted", "Candidate browser could not reach the SERPS server.", undefined, 1, 0,
            { interruption_started_at: new Date(priorInterruption).toISOString(), last_successful_acknowledgement: priorAck ? new Date(priorAck).toISOString() : null });
          await emit("connectivity_restored", "Candidate session reconnected to the SERPS server.", undefined, 1, 0,
            { interruption_ended_at: new Date(now).toISOString(), interruption_duration_ms: duration, readiness_revalidated: !requiredMonitoringUnavailable });
          if (!requiredMonitoringUnavailable) clearProtectedState("connectivity_interrupted", { interruption_duration_ms: duration, readiness_revalidated: true });
        }
      } catch {
        if (disposed) return;
        connectivityFailures.current += 1;
        if (connectivityFailures.current >= 2 && interruptionStartedAt.current == null) {
          interruptionStartedAt.current = Date.now();
          enterProtectedState("connectivity_interrupted", {
            established_after_failed_checks: connectivityFailures.current,
            last_successful_acknowledgement: lastServerAckAt.current ? new Date(lastServerAckAt.current).toISOString() : null,
          });
        }
      }
    };
    void checkServer();
    const interval = window.setInterval(() => void checkServer(), 10000);
    return () => { disposed = true; window.clearInterval(interval); };
  }, [workspace, finished, emit, enterProtectedState, clearProtectedState, requiredMonitoringUnavailable]);

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

  async function configureDemoPhonePolicy(armed: boolean) {
    try {
      const result = await updateDemoPhonePolicy(sessionId, armed);
      setDemoPhonePolicyArmed(result.demo_phone_policy_armed);
      if (!armed) {
        await emit("demo_protection_recovered", "Prototype demonstration protection was manually ended.", undefined, 1, 0, {
          demonstration_override: true,
          misconduct_determination: false,
        });
        clearProtectedState("policy_review", { demonstration_override: true }, true);
      }
      setStatus(armed ? "Prototype demo phone-protection policy armed. Persistent contextual phone evidence is required." : "Prototype demo phone-protection policy disarmed.");
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "Demo policy configuration could not be changed.");
    }
  }


  if (loading) return <section className="workspace-shell"><LoadingState label="Loading authorised demonstration workspace..." /></section>;
  if (error || !workspace) return <section className="workspace-shell"><ErrorState message={error || "Workspace unavailable."} /></section>;
  const protectionStatus = protection.reason === "connectivity_interrupted" ? "Connectivity interrupted"
    : protection.reason === "policy_review" ? "Policy review required" : "Monitoring verification required";
  const controlsDisabled = interactionDisabled(protection, monitoringProtectionActive, finished) || !!identityRequirement?.required;
  return <section className="workspace-shell">
    <header className="workspace-header">
      <div><p className="eyebrow dark">Assessment Demonstration Harness</p><h1>{workspace.examination.title}</h1><p>{workspace.candidate.full_name} · {workspace.institution.name} · Session {workspace.session.session_id}</p></div>
      <div className="timer" role="timer" aria-live="off"><span>Elapsed demonstration time</span><strong>{elapsed}</strong></div>
    </header>
    <aside className="monitoring-notice" role="note"><strong>Monitoring notice:</strong> SERPS performs bounded local object and sound-activity analysis. Raw audio and raw video are not stored by default. Evidence informs human review and never determines misconduct or terminates an examination.</aside>
    <p className="workflow-status" role="status" aria-live="polite">{status}</p>
    <p className="freshness-note">Candidate device heartbeat: {finished ? "monitoring stopped" : lastHeartbeat ? new Date(lastHeartbeat).toLocaleTimeString() : "awaiting first update"}</p>
    <p className="mode-disclosure"><strong>Proctoring mode:</strong> {modeDescription[workspace.session.deployment_mode]}</p>
    {demoControlsEnabled && protection.mode !== "PROTECTED" && <aside className="demo-policy-control" role="note"><div><strong>Prototype demonstration configuration</strong><p>Phone evidence remains logged. Policy protection is applied only when this demo control is armed and at least two phone-positive EvidenceEvents occur in the bounded contextual window.</p></div><button type="button" onClick={() => void configureDemoPhonePolicy(!demoPhonePolicyArmed)}>{demoPhonePolicyArmed ? "Disable phone-protection demonstration" : "Enable phone-protection demonstration"}</button></aside>}
    {identityRequirement?.required && <aside className="identity-prompt" role="alert"><div><strong>Identity assurance required by institutional policy</strong><p>{reauthenticationMessage(identityRequirement)}</p></div>{identityRequirement.state !== "manual_review" && <button className="primary-action" onClick={() => setIdentityCheckOpen(true)}>Verify identity</button>}</aside>}
    {identityCheckOpen && <FacialVerification examination={{ sessionId, primaryStream: () => streamByRole.current.primary ?? null, onReturn: () => { setIdentityCheckOpen(false); void refreshIdentityRequirement().catch(() => undefined); } }} /> }
    {requiredMonitoringUnavailable && <aside className="inline-warning" role="alert"><strong>{demoPhonePolicyArmed ? "Assessment interaction paused:" : "Monitoring readiness notice:"}</strong> required monitoring is unavailable. Restore the indicated camera, microphone or face-monitoring component to continue. {demoPhonePolicyArmed ? "The session remains active for human-governed review." : "Protection remains inactive while the demonstration policy is disarmed."}</aside>}

    <section className="dual-camera-grid workspace-cameras">
      <article className="camera-panel"><div className="camera-title"><h2>Primary camera</h2><StatusBadge label={finished ? "stopped" : primaryState} tone={finished ? "neutral" : primaryState === "connected" ? "success" : "danger"} /></div><video ref={primaryVideo} autoPlay muted playsInline aria-label="Primary candidate-facing live local preview" /><p>Candidate-facing face and upper-body view.</p><div className="detector-readout"><strong>Object detector: {finished ? "stopped" : objectStates.primary}</strong><span>{finished ? "Monitoring completed" : objectSummary.primary}</span></div></article>
      <article className="camera-panel"><div className="camera-title"><h2>Secondary camera</h2><StatusBadge label={finished ? "stopped" : workspace.session.deployment_mode === "B" ? secondaryState : `not used in Mode ${workspace.session.deployment_mode}`} tone={finished ? "neutral" : secondaryState === "connected" && workspace.session.deployment_mode === "B" ? "success" : "warning"} /></div><video ref={secondaryVideo} autoPlay muted playsInline aria-label="Secondary room or side-angle live local preview" /><p>Room, desk or side-angle environmental view.</p><div className="detector-readout"><strong>Object detector: {finished ? "stopped" : workspace.session.deployment_mode === "B" ? objectStates.secondary : "not used"}</strong><span>{finished ? "Monitoring completed" : workspace.session.deployment_mode === "B" ? objectSummary.secondary : "No independent secondary evidence expected"}</span></div></article>
    </section>

    <section className="multimodal-status-grid" aria-label="Multimodal detector status">
      <article className="card"><span className="badge">Local object intelligence</span><h2>{OBJECT_MODEL_NAME}</h2><p>Model version {OBJECT_MODEL_VERSION}; sampled every {OBJECT_SAMPLE_INTERVAL_MS / 1000} seconds for person and mobile-phone classes only.</p></article>
      <article className="card"><span className="badge">Privacy-safe audio activity</span><h2>Microphone: {finished ? "stopped" : audioState}</h2><p>{AUDIO_MONITOR_NAME} {AUDIO_MONITOR_VERSION}; current normalised RMS level {audioLevel.toFixed(4)}. No recording or transcription is performed.</p></article>
    </section>
    <div className="capability-disclosure"><strong>{finished ? "Face monitoring: Stopped when the demonstration completed." : faceCapability}</strong></div>
    <aside className="metadata-only-notice"><strong>Reviewer boundary:</strong> reviewer and administrator portals receive structured event metadata, CIE explanations and policy outcomes—not remote live media feeds.</aside>

    <section className="question-workspace" aria-labelledby="question-title">
      <div className="question-progress">Question {question + 1} of {questions.length}</div>
      <h2 id="question-title">{questions[question].prompt}</h2>
      <fieldset disabled={controlsDisabled}><legend className="sr-only">Choose one answer</legend>{questions[question].options.map((option, index) => <label className="answer-option" key={option}><input type="radio" name={`question-${question}`} checked={answers[question] === index} onChange={() => setAnswers((current) => ({ ...current, [question]: index }))} />{option}</label>)}</fieldset>
      <div className="question-actions"><button disabled={controlsDisabled || question === 0} onClick={() => setQuestion((value) => Math.max(0, value - 1))}>Previous</button><button disabled={controlsDisabled || question === questions.length - 1} onClick={() => setQuestion((value) => Math.min(questions.length - 1, value + 1))}>Next</button><button className="danger-action" disabled={controlsDisabled} onClick={() => setFinishOpen(true)}>Finish demonstration</button></div>
    </section>
    {finished && <section className="state-card" role="status"><StatusBadge label="Completed" tone="success" /><h2>Demonstration finished</h2><p>The session is now available in reviewer and administrator operational views.</p></section>}
    <ConfirmationDialog open={finishOpen} title="Finish this demonstration?" detail="This completes the session and stops camera, object-detector and microphone resources. Evidence and governance records remain append-only." confirmLabel="Finish demonstration" onConfirm={() => void finish()} onCancel={() => setFinishOpen(false)} />
    {protection.mode === "PROTECTED" && <div className="examination-protection-overlay" role="alertdialog" aria-live="assertive" aria-modal="true" aria-labelledby="protection-title"><div className="protection-panel"><span className="protection-shield" aria-hidden="true">◆</span><p className="eyebrow">{protectionStatus}</p><h2 id="protection-title">EXAMINATION CONTENT TEMPORARILY PROTECTED</h2><p>SERPS has detected a monitoring or policy condition requiring verification. Examination content has been temporarily concealed and the assessment timer paused. The session will resume when the applicable monitoring or governance condition is restored.</p><strong>Timer paused at {elapsed}</strong><p className="protection-boundary">This operational response is not a misconduct determination. Human review authority is preserved.</p>{canDemoRestore(demoControlsEnabled, demoPhonePolicyArmed, protection.reason) && <button type="button" className="demo-restore-action" onClick={() => void configureDemoPhonePolicy(false)}>Demo: restore examination</button>}</div></div>}
  </section>;
}

export default function DemonstrationWorkspacePage() {
  return <PortalShell allowedRoles={["Candidate"]} title="Demonstration Examination Workspace" badge="Candidate" summary="A bounded monitored assessment harness; not a complete CBT platform or secure browser."><DemonstrationWorkspacePageContent /></PortalShell>;
}
