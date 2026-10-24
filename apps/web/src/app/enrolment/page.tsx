"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import type { FaceCapture, LivenessAction } from "../../lib/contracts";
import { cameraAccessMessage, detectedOrientation, directionSymbol, instructionFor, observeFace, openIdentityCamera, poseIsValid, readCameraPermission, supportsFaceDetection, type CameraPermissionState, type FaceObservation } from "../../lib/biometrics";
import { cameraLabel, persistIdentityCamera, readIdentityCamera } from "../../lib/cameraRoles";
import { LocalFaceLandmarker } from "../../lib/faceDetection";
import { submitEnrollment } from "../../lib/api";
import { ENROLMENT_PROGRESS_KEY, readEnrolmentProgress, writeEnrolmentProgress } from "../../lib/enrolmentProgress";

const poses = ["forward", "left", "right", "up", "down", "centre_confirmation"];
const HOLD_MS = 900;
const CAMERA_SESSION_TIMEOUT_MS = 25 * 60 * 1000;

export default function EnrolmentPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectorRef = useRef<LocalFaceLandmarker | null>(null);
  const loopRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const runGenerationRef = useRef(0);
  const cameraOpeningRef = useRef(false);
  const poseRef = useRef<string | undefined>(undefined);
  const stableSinceRef = useRef<number | null>(null);
  const lastActionAt = useRef(0);
  const checkpointLoadedRef = useRef(false);
  const [observation, setObservation] = useState<FaceObservation | null>(null);
  const [captures, setCaptures] = useState<FaceCapture[]>([]);
  const [liveness, setLiveness] = useState<LivenessAction[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [cameraConfirmed, setCameraConfirmed] = useState(false);
  const [status, setStatus] = useState("Choose the candidate-facing camera to begin.");
  const [retryCount, setRetryCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [permissionState, setPermissionState] = useState<CameraPermissionState>("unsupported");
  const [detectorStatus, setDetectorStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [modelLoadMs, setModelLoadMs] = useState<number | null>(null);
  const [processingTimes, setProcessingTimes] = useState<number[]>([]);
  const [stableMs, setStableMs] = useState(0);
  const [viewportWidth, setViewportWidth] = useState(0);
  const pose = captures.length < poses.length ? poses[captures.length] : actions[liveness.length];
  const selectedCamera = cameras.find((camera) => camera.deviceId === selectedCameraId);

  const releaseResources = useCallback(() => {
    runGenerationRef.current += 1;
    if (loopRef.current != null) window.clearInterval(loopRef.current);
    if (timeoutRef.current != null) window.clearTimeout(timeoutRef.current);
    loopRef.current = null;
    timeoutRef.current = null;
    detectorRef.current?.close();
    detectorRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(() => { poseRef.current = pose; }, [pose]);
  useEffect(() => {
    if (!checkpointLoadedRef.current) return;
    const subject = sessionStorage.getItem("serps_enrollment_subject");
    if (subject) writeEnrolmentProgress(localStorage, { subject, captures, liveness: [], actions, retryCount });
  }, [captures, liveness, actions, retryCount]);
  useEffect(() => {
    const onResize = () => setViewportWidth(window.innerWidth);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const discoverCameras = useCallback(async (requestPermission: boolean) => {
    if (!navigator.mediaDevices?.enumerateDevices || !navigator.mediaDevices.getUserMedia) throw new Error("Camera APIs are unavailable.");
    const before = await readCameraPermission();
    setPermissionState(before);
    if (before === "denied") throw new Error("Camera access was denied. Allow camera permission in your browser settings and try again.");
    if (requestPermission) {
      let permission: MediaStream | null = null;
      try { permission = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); }
      catch (error) { setPermissionState(await readCameraPermission()); throw new Error(cameraAccessMessage(error), { cause: error }); }
      finally { permission?.getTracks().forEach((track) => track.stop()); }
      setPermissionState("granted");
    }
    const devices = (await navigator.mediaDevices.enumerateDevices()).filter((device) => device.kind === "videoinput");
    setCameras(devices);
    const preferred = readIdentityCamera(devices);
    if (preferred) {
      setSelectedCameraId(preferred.deviceId);
      setStatus(`Candidate-facing preference found: ${cameraLabel(preferred)}. Confirm before opening the stream.`);
    } else if (devices.length === 1) {
      setSelectedCameraId(devices[0].deviceId);
      setStatus(`One camera found: ${cameraLabel(devices[0], "Camera 1")}. Confirm before opening the stream.`);
    } else {
      setSelectedCameraId("");
      setStatus(devices.length ? "Camera labels are ambiguous. Select the candidate-facing camera manually." : "No camera was discovered.");
    }
    setCameraConfirmed(false);
  }, []);

  useEffect(() => {
    const token = sessionStorage.getItem("serps_enrollment_token");
    const required = JSON.parse(sessionStorage.getItem("serps_enrollment_actions") ?? "[]") as string[];
    const recoveryNotice = sessionStorage.getItem("serps_enrollment_notice");
    const subject = sessionStorage.getItem("serps_enrollment_subject") ?? "";
    const initialise = window.setTimeout(() => {
      setActions(required);
      const checkpoint = subject ? readEnrolmentProgress(localStorage, subject, poses, required) : null;
      if (checkpoint) {
        setCaptures(checkpoint.captures);
        setLiveness(checkpoint.liveness);
        setRetryCount(checkpoint.retryCount);
      }
      checkpointLoadedRef.current = true;
      sessionStorage.removeItem("serps_enrollment_notice");
      if (!token || required.length < 3) {
        setStatus("The enrolment session is missing or expired. Return to registration.");
      } else if (!supportsFaceDetection()) {
        setDetectorStatus("error");
        setStatus("This browser cannot run the local WebAssembly camera detector.");
      } else {
        void discoverCameras(false).then(() => {
          if (checkpoint && checkpoint.captures.length + checkpoint.liveness.length > 0) setStatus(`Restored ${checkpoint.captures.length + checkpoint.liveness.length} validated observation(s). Confirm the camera to continue.`);
          else if (recoveryNotice) setStatus(recoveryNotice);
        }).catch((error) => setStatus(error instanceof Error ? error.message : "Grant camera access to identify the candidate-facing camera."));
      }
    }, 0);
    return () => { window.clearTimeout(initialise); releaseResources(); };
  }, [discoverCameras, releaseResources]);

  async function startEnrolmentCamera() {
    if (!selectedCamera || !videoRef.current || cameraOpeningRef.current) return;
    cameraOpeningRef.current = true;
    const runGeneration = ++runGenerationRef.current;
    setBusy(true);
    setCameraConfirmed(true);
    setDetectorStatus("loading");
    setStatus(`Opening candidate-facing camera: ${cameraLabel(selectedCamera)}...`);
    try {
      persistIdentityCamera(selectedCamera);
      const stream = await openIdentityCamera(videoRef.current, selectedCamera.deviceId);
      if (runGeneration !== runGenerationRef.current) { stream.getTracks().forEach((track) => track.stop()); return; }
      streamRef.current = stream;
      setCameraActive(true);
      streamRef.current.getVideoTracks()[0].addEventListener("ended", () => {
        setCameraActive(false);
        setObservation(null);
        setStatus("Camera access ended.");
        releaseResources();
      });
      setStatus("Loading the locally bundled face landmarker...");
      const detector = new LocalFaceLandmarker();
      detectorRef.current = detector;
      await detector.initialise();
      if (runGeneration !== runGenerationRef.current) { detector.close(); return; }
      setModelLoadMs(detector.modelLoadTime);
      setDetectorStatus("ready");
      setStatus("Detector ready. Face forward inside the responsive guide.");
      loopRef.current = window.setInterval(() => {
        if (!videoRef.current || !canvasRef.current || videoRef.current.readyState < 2 || !detectorRef.current) return;
        void observeFace(videoRef.current, canvasRef.current, detectorRef.current).then((value) => {
          setObservation(value);
          setProcessingTimes((items) => [...items.slice(-29), value.processingTime]);
          const currentPose = poseRef.current;
          const valid = !!currentPose && poseIsValid(currentPose, value);
          if (!valid) {
            stableSinceRef.current = null;
            setStableMs(0);
            return;
          }
          if (stableSinceRef.current == null) stableSinceRef.current = performance.now();
          setStableMs(performance.now() - stableSinceRef.current);
        }).catch((error) => {
          setDetectorStatus("error");
          setStatus(error instanceof Error ? error.message : "Local face analysis failed.");
        });
      }, 220);
      timeoutRef.current = window.setTimeout(() => {
        releaseResources();
        setCameraActive(false);
        setCameraConfirmed(false);
        setStatus("The camera was released after 25 minutes. Your validated observations remain checkpointed; confirm the camera to continue.");
      }, CAMERA_SESSION_TIMEOUT_MS);
    } catch (error) {
      if (runGeneration !== runGenerationRef.current) return;
      releaseResources();
      setCameraActive(false);
      setCameraConfirmed(false);
      setDetectorStatus("error");
      setStatus(error instanceof Error ? error.message : "Camera or detector initialisation failed.");
    } finally {
      cameraOpeningRef.current = false;
      setBusy(false);
    }
  }

  async function refreshCameras() {
    if (busy) return;
    setBusy(true);
    setStatus(permissionState === "granted" ? "Refreshing available cameras..." : "Requesting browser camera access...");
    try {
      await discoverCameras(permissionState !== "granted");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : cameraAccessMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function finish(finalCaptures: FaceCapture[], finalLiveness: LivenessAction[]) {
    const token = sessionStorage.getItem("serps_enrollment_token");
    if (!token) return;
    setBusy(true);
    setStatus("Saving the derived experimental similarity representation...");
    try {
      await submitEnrollment({ enrollment_token: token, captures: finalCaptures, liveness_actions: finalLiveness, retry_count: retryCount });
      sessionStorage.removeItem("serps_enrollment_token");
      sessionStorage.removeItem("serps_enrollment_actions");
      sessionStorage.removeItem("serps_enrollment_subject");
      localStorage.removeItem(ENROLMENT_PROGRESS_KEY);
      releaseResources();
      setCameraActive(false);
      setStatus("Facial enrolment complete. Camera released; continue to password sign-in.");
      window.setTimeout(() => { window.location.href = "/login"; }, 1400);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Enrolment could not be completed.");
      setRetryCount((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  function captureCurrent() {
    if (!observation || !pose || busy || stableMs < HOLD_MS || !poseIsValid(pose, observation)) return;
    stableSinceRef.current = null;
    setStableMs(0);
    if (captures.length < poses.length) {
      const next = [...captures, { pose, descriptor: observation.descriptor, one_face: true, pose_validated: true, lighting_score: observation.lightingScore, distance_score: observation.distanceScore, confidence: observation.confidence }];
      setCaptures(next);
      setStatus(next.length === poses.length ? "Six-direction capture complete. Begin the unpredictable movement sequence." : `${instructionFor(pose)} accepted after a stable hold.`);
      return;
    }
    const now = Date.now();
    if (lastActionAt.current && now - lastActionAt.current < 500) {
      setStatus("Move deliberately between prompts; rapid static submissions are not accepted.");
      return;
    }
    lastActionAt.current = now;
    const action: LivenessAction = { action: pose, completed: true, confidence: observation.confidence, timestamp: new Date(now).toISOString() };
    const next = [...liveness, action];
    setLiveness(next);
    if (next.length === actions.length) setStatus("All nine observations are validated. Select Complete facial enrolment to submit them securely.");
    else setStatus(`${instructionFor(pose)} accepted. Move to the next prompt.`);
  }

  function retry() {
    setCaptures([]);
    setLiveness([]);
    setRetryCount((value) => value + 1);
    stableSinceRef.current = null;
    lastActionAt.current = 0;
    setStableMs(0);
    setStatus("Capture reset. Face forward inside the guide.");
  }

  function cancel() {
    releaseResources();
    setCameraActive(false);
    sessionStorage.removeItem("serps_enrollment_token");
    sessionStorage.removeItem("serps_enrollment_actions");
    sessionStorage.removeItem("serps_enrollment_subject");
    localStorage.removeItem(ENROLMENT_PROGRESS_KEY);
    window.location.href = "/register";
  }

  const completed = captures.length + liveness.length;
  const total = poses.length + actions.length;
  const captureComplete = total > poses.length && completed === total;
  const averageMs = processingTimes.length ? processingTimes.reduce((sum, item) => sum + item, 0) / processingTimes.length : null;
  const poseReady = !!observation && !!pose && poseIsValid(pose, observation) && stableMs >= HOLD_MS;
  const disabledReason = !cameraActive ? "Camera stream is required" : detectorStatus !== "ready" ? "Local detector must finish loading" : !observation?.oneFace ? "Exactly one face is required" : !pose || !poseIsValid(pose, observation) ? "Match the requested orientation and quality guidance" : stableMs < HOLD_MS ? "Hold the correct pose steadily" : undefined;
  const box = observation?.boundingBox;
  const guideWidth = box ? Math.min(74, Math.max(48, box.width * 145 * 100)) : viewportWidth < 680 ? 68 : 58;
  const guideHeight = box ? Math.min(90, Math.max(64, box.height * 128 * 100)) : 82;
  const guideStyle = {
    "--guide-width": `${guideWidth}%`,
    "--guide-height": `${guideHeight}%`,
    "--guide-stroke": `${Math.max(3, Math.round((typeof window === "undefined" ? 1 : window.devicePixelRatio || 1) * 2))}px`,
  } as CSSProperties;

  return <main className="page-shell biometric-page">
    <section className="biometric-header"><span className="badge">Facial enrolment</span><h1>Guided identity capture</h1><p>Directions refer to your own left and right, not the screen. The preview is mirrored for natural interaction; detection uses the original camera coordinates.</p></section>
    {!cameraActive && <section className="card identity-camera-choice" aria-label="Facial enrolment camera selection">
      <span className="badge">Candidate-facing camera</span>
      <h2>Facial enrolment camera: {cameraLabel(selectedCamera)}</h2>
      <p>The integrated or front-facing camera is preferred. A USB environmental camera is never selected by enumeration order.</p>
      <label>Camera<select aria-label="Facial enrolment camera" value={selectedCameraId} onChange={(event) => { setSelectedCameraId(event.target.value); setCameraConfirmed(false); }}>
        <option value="">Select the candidate-facing camera</option>
        {cameras.map((camera, index) => <option key={camera.deviceId} value={camera.deviceId}>{cameraLabel(camera, `Camera ${index + 1}`)}</option>)}
      </select></label>
      <p className="field-help">Camera permission: {permissionState === "unsupported" ? "browser status unavailable" : permissionState}. Permission does not guarantee that a busy camera can be opened.</p>
      <div className="camera-role-actions"><button type="button" disabled={busy} onClick={() => void refreshCameras()}>{busy ? "Checking cameras..." : permissionState === "granted" ? "Refresh available cameras" : "Grant camera access"}</button><button type="button" className="primary-action" disabled={!selectedCameraId || busy} onClick={() => void startEnrolmentCamera()}>{busy ? "Opening camera..." : "Confirm and start facial enrolment"}</button><button type="button" disabled={busy} onClick={cancel}>Cancel and return</button></div>
      <p className="form-note" role="status">{status}</p>
    </section>}
    <section className="biometric-layout" hidden={!cameraConfirmed}>
      <article className="camera-capture-card">
        <div className="camera-guide" style={guideStyle}>
          <video className="mirrored-preview" ref={videoRef} autoPlay muted playsInline aria-label="Mirrored local facial enrolment preview" />
          <div className="face-guide" aria-hidden="true" />
          <div className="pose-instruction"><span className="direction-arrow" aria-hidden="true">{pose ? directionSymbol(pose) : "✓"}</span><strong>{pose ? instructionFor(pose) : "All observations captured"}</strong></div>
        </div>
        <canvas ref={canvasRef} hidden />
        <p className="direction-note">Directions refer to your own left and right, not the screen.</p>
        <div className="quality-row"><span className={cameraActive ? "quality-pass" : "quality-warn"}>Camera {cameraActive ? "active" : "inactive"}</span><span className={detectorStatus === "ready" ? "quality-pass" : "quality-warn"}>Detector {detectorStatus}</span><span>{observation?.faceCount === 1 ? "One face" : observation?.faceCount === 0 ? "No face" : observation ? `${observation.faceCount} faces` : "Checking face"}</span><span>Face illumination {observation ? `${Math.round(observation.lightingScore * 100)}%` : "Not measured"}</span><span>Distance {observation ? `${Math.round(observation.distanceScore * 100)}%` : "Not measured"}</span></div>
        <div className="orientation-feedback"><span>Instruction: <strong>{pose ? `${directionSymbol(pose)} ${instructionFor(pose)}` : "Complete"}</strong></span><span>Detected: <strong>{captureComplete ? "All required observations validated" : detectedOrientation(observation)}</strong></span>{!captureComplete && <span>Hold still: <strong>{(Math.min(HOLD_MS, stableMs) / 1000).toFixed(1)} / {(HOLD_MS / 1000).toFixed(1)} seconds</strong></span>}</div>
        <p className="live-guidance" role="status">{captureComplete ? status : observation?.feedback ?? status}</p>
        {captureComplete ? <button className="primary-action" disabled={busy} onClick={() => void finish(captures, liveness)}>{busy ? "Submitting enrolment..." : "Complete facial enrolment"}</button> : <button className="primary-action" disabled={busy || !poseReady} title={disabledReason} onClick={captureCurrent}>{captures.length < poses.length ? "Accept stable pose" : "Accept liveness movement"}</button>}
      </article>
      <aside className="card biometric-progress"><h2>Enrolment progress</h2><progress value={completed} max={total || 1}>{completed}/{total}</progress><p>{completed} of {total || "—"} validated observations</p><p className="privacy-note">Validated fixed observations are checkpointed in this browser for account-bound recovery after reload or closure. Dynamic liveness restarts after interruption. Raw images and video are not stored.</p><dl className="detector-metrics"><div><dt>Facial camera</dt><dd>{cameraLabel(selectedCamera)}</dd></div><div><dt>Model load</dt><dd>{modelLoadMs == null ? "Loading" : `${Math.round(modelLoadMs)} ms`}</dd></div><div><dt>Average processing</dt><dd>{averageMs == null ? "Waiting" : `${averageMs.toFixed(1)} ms`}</dd></div><div><dt>Retries</dt><dd>{retryCount}</dd></div></dl><ol>{poses.map((item, index) => <li className={index < captures.length ? "complete" : index === captures.length ? "current" : ""} key={item}>{directionSymbol(item)} {instructionFor(item)}</li>)}</ol>{captures.length === poses.length && <><h3>Dynamic liveness</h3><ol>{actions.map((item, index) => <li className={index < liveness.length ? "complete" : index === liveness.length ? "current" : ""} key={`${item}-${index}`}>{directionSymbol(item)} {instructionFor(item)}</li>)}</ol></>}<p className="form-note">{status}</p><div className="dialog-actions"><button onClick={retry} disabled={busy}>Retry</button><button onClick={cancel}>Cancel and release camera</button></div></aside>
    </section>
  </main>;
}
