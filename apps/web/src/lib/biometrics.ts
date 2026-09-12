import type { LocalFaceLandmarker } from "./faceDetection";

export type FaceObservation = {
  descriptor: number[]; oneFace: boolean; faceCount: number; centreX: number; centreY: number;
  lightingScore: number; distanceScore: number; confidence: number; feedback: string;
  yawEstimate: number | null; pitchEstimate: number | null; rollEstimate: number | null; processingTime: number;
  boundingBox: { x: number; y: number; width: number; height: number } | null;
};

export function supportsFaceDetection(): boolean { return typeof window !== "undefined" && typeof WebAssembly !== "undefined" && !!navigator.mediaDevices?.getUserMedia; }

export type CameraPermissionState = "granted" | "denied" | "prompt" | "unsupported";

export async function readCameraPermission(): Promise<CameraPermissionState> {
  if (!navigator.permissions?.query) return "unsupported";
  try {
    const result = await navigator.permissions.query({ name: "camera" as PermissionName });
    return result.state;
  } catch {
    return "unsupported";
  }
}

export function cameraAccessMessage(error: unknown): string {
  const name = error instanceof DOMException ? error.name : error instanceof Error ? error.name : "";
  if (name === "NotAllowedError" || name === "SecurityError") return "Camera access was denied. Allow camera permission in your browser settings and try again.";
  if (name === "NotFoundError" || name === "DevicesNotFoundError") return "No compatible camera was found. Connect a camera and refresh the device list.";
  if (name === "NotReadableError" || name === "TrackStartError") return "The selected camera could not be opened. It may already be in use by another browser or application. Close other camera sessions and try again.";
  if (name === "OverconstrainedError" || name === "ConstraintNotSatisfiedError") return "The selected camera does not satisfy the required video settings. Choose another camera or refresh the device list.";
  if (name === "AbortError" || name === "InvalidStateError") return "The selected camera is no longer available. Refresh the camera list and select another device.";
  return "Unable to access the selected camera. Check browser permission and whether another application is using the device, then try again.";
}

export async function openIdentityCamera(video: HTMLVideoElement, deviceId: string): Promise<MediaStream> {
  if (!deviceId) throw new Error("Choose and confirm the candidate-facing camera before continuing.");
  let stream: MediaStream | null = null;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId }, width: { ideal: 960 }, height: { ideal: 720 } }, audio: false });
    video.srcObject = stream;
    await video.play();
    return stream;
  } catch (error) {
    stream?.getTracks().forEach((track) => track.stop());
    video.srcObject = null;
    throw new Error(cameraAccessMessage(error), { cause: error });
  }
}

function clamp(value: number): number { return Math.max(0, Math.min(1, value)); }

export async function observeFace(video: HTMLVideoElement, canvas: HTMLCanvasElement, detector: LocalFaceLandmarker): Promise<FaceObservation> {
  const detected = detector.detect(video);
  const empty = { descriptor: [], oneFace: false, faceCount: detected.faceCount, centreX: 0, centreY: 0, lightingScore: 0, distanceScore: 0, confidence: 0, yawEstimate: null, pitchEstimate: null, rollEstimate: null, processingTime: detected.processingTime, boundingBox: null };
  if (detected.faceCount === 0) return { ...empty, feedback: "No face detected" };
  if (detected.faceCount > 1) return { ...empty, feedback: "Multiple faces detected" };
  if (!detected.boundingBox || !detected.faceCentre || detected.faceSize == null) return { ...empty, feedback: "Face geometry unavailable" };
  const box = detected.boundingBox; const width = video.videoWidth || 1; const height = video.videoHeight || 1;
  canvas.width = 8; canvas.height = 8; const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) throw new Error("Camera analysis is unavailable in this browser.");
  const x = Math.max(0, box.x * width); const y = Math.max(0, box.y * height); const cropWidth = Math.min(width - x, box.width * width); const cropHeight = Math.min(height - y, box.height * height);
  context.drawImage(video, x, y, cropWidth, cropHeight, 0, 0, 8, 8);
  const pixels = context.getImageData(0, 0, 8, 8).data; const descriptor: number[] = []; let brightness = 0;
  for (let index = 0; index < pixels.length; index += 4) { const luminance = (0.2126 * pixels[index] + 0.7152 * pixels[index + 1] + 0.0722 * pixels[index + 2]) / 255; descriptor.push(Number(luminance.toFixed(5))); brightness += luminance; }
  // Face-region luminance only: 0.55 is the neutral target and the existing
  // 0.45 quality gate is intentionally conservative pending controlled calibration.
  brightness /= 64; const lightingScore = clamp(1 - Math.abs(brightness - 0.55) / 0.55); const distanceScore = clamp(1 - Math.abs(detected.faceSize - 0.24) / 0.24);
  const centred = Math.abs(detected.faceCentre.x - 0.5) < 0.16 && Math.abs(detected.faceCentre.y - 0.5) < 0.18;
  let feedback = "Hold still";
  if (lightingScore < 0.45) feedback = "Improve face illumination"; else if (detected.faceSize < 0.12) feedback = "Move closer"; else if (detected.faceSize > 0.42) feedback = "Move farther away"; else if (detected.faceCentre.y > 0.59) feedback = "Raise your head slightly"; else if (detected.faceCentre.y < 0.41) feedback = "Lower your head slightly"; else if (!centred) feedback = "Centre your face";
  return { descriptor, oneFace: true, faceCount: 1, centreX: detected.faceCentre.x, centreY: detected.faceCentre.y, lightingScore, distanceScore, confidence: Math.min(lightingScore, distanceScore), feedback, yawEstimate: detected.yawEstimate, pitchEstimate: detected.pitchEstimate, rollEstimate: detected.rollEstimate, processingTime: detected.processingTime, boundingBox: detected.boundingBox };
}

export function poseIsValid(pose: string, observation: FaceObservation): boolean {
  if (!observation.oneFace || observation.lightingScore < 0.45 || observation.distanceScore < 0.45 || observation.yawEstimate == null || observation.pitchEstimate == null || observation.rollEstimate == null || Math.abs(observation.rollEstimate) > 15) return false;
  // Detection uses the original, unmirrored video. Candidate-right appears on
  // the camera image's left, so negative yaw is candidate-relative right.
  if (pose === "left" || pose === "turn_left") return observation.yawEstimate > 0.16;
  if (pose === "right" || pose === "turn_right") return observation.yawEstimate < -0.16;
  if (pose === "up" || pose === "look_up") return observation.pitchEstimate < -0.12;
  if (pose === "down" || pose === "look_down") return observation.pitchEstimate > 0.12;
  return Math.abs(observation.yawEstimate) < 0.11 && Math.abs(observation.pitchEstimate) < 0.11;
}

export function detectedOrientation(observation: FaceObservation | null): string {
  if (!observation?.oneFace) return "Unavailable";
  if ((observation.yawEstimate ?? 0) < -0.16) return "Turning right"; if ((observation.yawEstimate ?? 0) > 0.16) return "Turning left";
  if ((observation.pitchEstimate ?? 0) < -0.12) return "Looking upward"; if ((observation.pitchEstimate ?? 0) > 0.12) return "Looking downward"; return "Centred";
}

export const directionSymbol = (pose: string): string => ({ forward: "●", centre_confirmation: "●", return_to_centre: "●", left: "←", turn_left: "←", right: "→", turn_right: "→", up: "↑", look_up: "↑", down: "↓", look_down: "↓" }[pose] ?? "●");

export const instructionFor = (pose: string): string => ({ forward: "Face forward", left: "Turn toward your left shoulder", right: "Turn toward your right shoulder", up: "Look upward", down: "Look downward", centre_confirmation: "Return to centre", turn_left: "Turn toward your left shoulder", turn_right: "Turn toward your right shoulder", look_up: "Look upward", look_down: "Look downward", return_to_centre: "Return to centre" }[pose] ?? pose.replaceAll("_", " "));
