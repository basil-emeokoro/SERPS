"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { fetchCurrentUser, submitFacialAuthentication, submitPeriodicVerification } from "../../lib/api";
import { detectedOrientation, directionSymbol, instructionFor, observeFace, openIdentityCamera, poseIsValid, supportsFaceDetection, type FaceObservation } from "../../lib/biometrics";
import { cameraLabel, persistIdentityCamera, readIdentityCamera } from "../../lib/cameraRoles";
import { LocalFaceLandmarker } from "../../lib/faceDetection";
import { facialVerificationDestination } from "../../lib/facialVerification";

const HOLD_MS = 1500;
const SESSION_TIMEOUT_MS = 10 * 60 * 1000;

export default function FacialAuthenticationPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectorRef = useRef<LocalFaceLandmarker | null>(null);
  const loopRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const runGenerationRef = useRef(0);
  const stableSinceRef = useRef<number | null>(null);
  const [observation, setObservation] = useState<FaceObservation | null>(null);
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [stableMs, setStableMs] = useState(0);
  const [status, setStatus] = useState("Preparing the identity camera...");
  const [retryCount, setRetryCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const prompt = "forward";
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

  const startCamera = useCallback(async (device: MediaDeviceInfo) => {
    if (!videoRef.current) return;
    const runGeneration = ++runGenerationRef.current;
    setBusy(true);
    setStatus(`Opening saved candidate-facing camera: ${cameraLabel(device)}...`);
    try {
      persistIdentityCamera(device);
      const stream = await openIdentityCamera(videoRef.current, device.deviceId);
      if (runGeneration !== runGenerationRef.current) { stream.getTracks().forEach((track) => track.stop()); return; }
      streamRef.current = stream;
      setCameraActive(true);
      streamRef.current.getVideoTracks()[0].addEventListener("ended", () => {
        releaseResources();
        setCameraActive(false);
        setStatus("Camera access ended.");
      });
      setStatus("Loading the local face landmarker...");
      const detector = new LocalFaceLandmarker();
      detectorRef.current = detector;
      await detector.initialise();
      if (runGeneration !== runGenerationRef.current) { detector.close(); return; }
      setStatus("Camera and detector ready. Hold one quality-valid forward-facing observation.");
      loopRef.current = window.setInterval(() => {
        if (!videoRef.current || !canvasRef.current || videoRef.current.readyState < 2 || !detectorRef.current) return;
        void observeFace(videoRef.current, canvasRef.current, detectorRef.current).then((value) => {
          setObservation(value);
          const valid = poseIsValid("forward", value);
          if (!valid) {
            stableSinceRef.current = null;
            setStableMs(0);
            return;
          }
          if (stableSinceRef.current == null) stableSinceRef.current = performance.now();
          setStableMs(performance.now() - stableSinceRef.current);
        }).catch((error) => setStatus(error instanceof Error ? error.message : "Face analysis failed."));
      }, 220);
      timeoutRef.current = window.setTimeout(() => {
        releaseResources();
        setCameraActive(false);
        setStatus("The facial-authentication challenge timed out. Camera resources were released.");
        window.location.href = "/login";
      }, SESSION_TIMEOUT_MS);
    } catch (error) {
      if (runGeneration !== runGenerationRef.current) return;
      releaseResources();
      setCameraActive(false);
      setStatus(error instanceof Error ? error.message : "Camera or detector initialisation failed.");
    } finally {
      setBusy(false);
    }
  }, [releaseResources]);

  useEffect(() => {
    const initialise = window.setTimeout(() => {
      if (!sessionStorage.getItem("serps_face_challenge")) {
        setStatus("The facial-authentication challenge is missing or expired. Return to sign-in.");
      } else if (!supportsFaceDetection()) {
        setStatus("Local WebAssembly face detection is unavailable in this browser.");
      } else {
        void navigator.mediaDevices.enumerateDevices().then((devices) => {
          const videoDevices = devices.filter((device) => device.kind === "videoinput");
          setCameras(videoDevices);
          const preferred = readIdentityCamera(videoDevices);
          if (preferred) {
            setSelectedCameraId(preferred.deviceId);
            void startCamera(preferred);
          } else if (videoDevices.length === 1) {
            setSelectedCameraId(videoDevices[0].deviceId);
            void startCamera(videoDevices[0]);
          } else {
            setStatus("The saved candidate-facing camera is unavailable. Select and confirm the primary camera.");
          }
        }).catch((error) => setStatus(error instanceof Error ? error.message : "Camera discovery failed."));
      }
    }, 0);
    return () => { window.clearTimeout(initialise); releaseResources(); };
  }, [releaseResources, startCamera]);

  async function verify(face: FaceObservation) {
    const challengeToken = sessionStorage.getItem("serps_face_challenge");
    const mode = sessionStorage.getItem("serps_face_mode") ?? "authentication";
    if (!challengeToken) return;
    setBusy(true);
    setStatus("Comparing the derived representation and validating liveness...");
    try {
      const payload = { challenge_token: challengeToken, descriptor: face.descriptor, one_face: face.oneFace, lighting_score: face.lightingScore, distance_score: face.distanceScore, retry_count: retryCount };
      const result = mode === "periodic" ? await submitPeriodicVerification(payload) : await submitFacialAuthentication(payload);
      const outcome = String(result.outcome ?? "Authentication Failed");
      setStatus(`${outcome}. Identity confidence: ${Math.round(Number(result.identity_confidence ?? 0) * 100)}%.`);
      if (outcome === "Verified") {
        ["serps_face_challenge", "serps_face_actions", "serps_face_mode"].forEach((key) => sessionStorage.removeItem(key));
        releaseResources();
        setCameraActive(false);
        if (mode === "periodic") {
          const returnPath = sessionStorage.getItem("serps_face_return") ?? "/candidate";
          sessionStorage.removeItem("serps_face_return");
          window.location.href = returnPath;
          return;
        }
        const accessToken = String(result.access_token);
        const refreshToken = String(result.refresh_token);
        sessionStorage.setItem("serps_access_token", accessToken);
        sessionStorage.setItem("serps_refresh_token", refreshToken);
        const user = await fetchCurrentUser(accessToken);
        sessionStorage.setItem("serps_current_user", JSON.stringify(user));
        window.location.href = facialVerificationDestination(user.roles);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Facial authentication failed.");
      setRetryCount((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  function completePrompt() {
    if (!observation || !prompt || busy || stableMs < HOLD_MS || !poseIsValid(prompt, observation)) return;
    stableSinceRef.current = null;
    setStableMs(0);
    void verify(observation);
  }

  function retry() {
    setRetryCount((value) => value + 1);
    stableSinceRef.current = null;
    setStableMs(0);
    setStatus("Observation reset. Hold one quality-valid forward-facing pose.");
  }

  function cancel() {
    releaseResources();
    setCameraActive(false);
    ["serps_face_challenge", "serps_face_actions", "serps_face_mode", "serps_face_return"].forEach((key) => sessionStorage.removeItem(key));
    window.location.href = "/login";
  }

  const box = observation?.boundingBox;
  const guideStyle = {
    "--guide-width": `${box ? Math.min(74, Math.max(48, box.width * 145 * 100)) : 58}%`,
    "--guide-height": `${box ? Math.min(90, Math.max(64, box.height * 128 * 100)) : 82}%`,
    "--guide-stroke": `${Math.max(3, Math.round((typeof window === "undefined" ? 1 : window.devicePixelRatio || 1) * 2))}px`,
  } as CSSProperties;
  const promptReady = !!observation && !!prompt && poseIsValid(prompt, observation) && stableMs >= HOLD_MS;

  return <main className="page-shell biometric-page">
    <section className="biometric-header"><span className="badge">Two-stage authentication</span><h1>Facial identity verification</h1><p>One quality-valid derived facial observation is compared with the enrolled representation. The mirrored preview does not alter detector coordinates.</p></section>
    {!cameraActive && <section className="card identity-camera-choice"><h2>Facial authentication camera: {cameraLabel(selectedCamera)}</h2><p>The saved candidate-facing primary camera is reused. If it is unavailable, select the correct replacement explicitly.</p><label>Candidate-facing camera<select value={selectedCameraId} onChange={(event) => setSelectedCameraId(event.target.value)}><option value="">Select primary camera</option>{cameras.map((camera, index) => <option key={camera.deviceId} value={camera.deviceId}>{cameraLabel(camera, `Camera ${index + 1}`)}</option>)}</select></label><div className="camera-role-actions"><button className="primary-action" disabled={!selectedCamera || busy} onClick={() => selectedCamera && void startCamera(selectedCamera)}>Confirm and open camera</button><button onClick={cancel}>Cancel and return</button></div><p className="form-note" role="status">{status}</p></section>}
    <section className="biometric-layout" hidden={!cameraActive}><article className="camera-capture-card"><div className="camera-guide" style={guideStyle}><video className="mirrored-preview" ref={videoRef} autoPlay muted playsInline aria-label="Mirrored local facial authentication preview" /><div className="face-guide" aria-hidden="true" /><div className="pose-instruction"><span className="direction-arrow" aria-hidden="true">{directionSymbol(prompt)}</span><strong>{instructionFor(prompt)}</strong></div></div><canvas ref={canvasRef} hidden /><p className="direction-note">Centre your face and hold still; failed quality checks do not consume the observation.</p><div className="quality-row"><span className={observation?.oneFace ? "quality-pass" : "quality-warn"}>{observation?.oneFace ? "One face" : observation?.feedback ?? "Checking face"}</span><span>Lighting {Math.round((observation?.lightingScore ?? 0) * 100)}%</span><span>Distance {Math.round((observation?.distanceScore ?? 0) * 100)}%</span></div><div className="orientation-feedback"><span>Required: <strong>1 validated observation</strong></span><span>Detected: <strong>{detectedOrientation(observation)}</strong></span><span>Hold still: <strong>{(Math.min(HOLD_MS, stableMs) / 1000).toFixed(1)} / {(HOLD_MS / 1000).toFixed(1)} seconds</strong></span></div><p className="live-guidance">{observation?.feedback ?? status}</p><button className="primary-action" disabled={busy || !promptReady} onClick={completePrompt}>{busy ? "Verifying identity..." : "Verify facial identity"}</button></article><aside className="card biometric-progress"><h2>Single-observation verification</h2><p>Camera: <strong>{cameraLabel(selectedCamera)}</strong></p><p>One accepted derived observation is compared with the stored enrolment representation.</p><p className="form-note" role="status">{status}</p><p className="privacy-note">Raw images, frame bytes, and video are not stored.</p><div className="dialog-actions"><button disabled={busy} onClick={retry}>Retry observation</button><button onClick={cancel}>Cancel and release camera</button></div></aside></section>
  </main>;
}
