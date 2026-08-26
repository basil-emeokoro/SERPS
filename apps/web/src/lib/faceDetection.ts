import type { NormalizedLandmark } from "@mediapipe/tasks-vision";

export type FaceBoundingBox = { x: number; y: number; width: number; height: number };
export type FaceGeometry = {
  boundingBox: FaceBoundingBox | null;
  faceCentre: { x: number; y: number } | null;
  faceSize: number | null;
};
export type LocalFaceResult = {
  detectorReady: boolean;
  faceCount: number;
  boundingBox: FaceBoundingBox | null;
  landmarks: NormalizedLandmark[];
  faceCentre: { x: number; y: number } | null;
  faceSize: number | null;
  yawEstimate: number | null;
  pitchEstimate: number | null;
  rollEstimate: number | null;
  confidence: number | null;
  processingTime: number;
  faces: FaceGeometry[];
};

type FaceLandmarkerInstance = import("@mediapipe/tasks-vision").FaceLandmarker;

export const FACE_WASM_PATH = "/mediapipe/wasm";
export const FACE_MODEL_PATH = "/mediapipe/models/face_landmarker.task";
export const FACE_PERCEPTION_NAME = "Local MediaPipe Face Landmarker";
export const FACE_PERCEPTION_VERSION = "0.10.35";
export const FACE_SAMPLE_INTERVAL_MS = 1500;
export const SUSTAINED_FACE_ABSENCE_MS = 6000;

function clamp(value: number): number { return Math.max(-1, Math.min(1, value)); }

export function deriveFaceGeometry(landmarks: NormalizedLandmark[]): Omit<LocalFaceResult, "detectorReady" | "faceCount" | "processingTime" | "confidence" | "faces"> {
  if (landmarks.length < 455) return { boundingBox: null, landmarks, faceCentre: null, faceSize: null, yawEstimate: null, pitchEstimate: null, rollEstimate: null };
  const xs = landmarks.map((item) => item.x); const ys = landmarks.map((item) => item.y);
  const left = Math.max(0, Math.min(...xs)); const right = Math.min(1, Math.max(...xs));
  const top = Math.max(0, Math.min(...ys)); const bottom = Math.min(1, Math.max(...ys));
  const width = Math.max(0.0001, right - left); const height = Math.max(0.0001, bottom - top);
  const nose = landmarks[1]; const leftEye = landmarks[33]; const rightEye = landmarks[263];
  const yawEstimate = clamp(((nose.x - (left + right) / 2) / width) * 2);
  const pitchEstimate = clamp((((nose.y - top) / height) - 0.5) * 2.4);
  const rollEstimate = Math.atan2(rightEye.y - leftEye.y, rightEye.x - leftEye.x) * 180 / Math.PI;
  return { boundingBox: { x: left, y: top, width, height }, landmarks, faceCentre: { x: (left + right) / 2, y: (top + bottom) / 2 }, faceSize: width * height, yawEstimate, pitchEstimate, rollEstimate };
}

export class LocalFacePerceptionService {
  private task: FaceLandmarkerInstance | null = null;
  private lastTimestamp = 0;
  modelLoadTime = 0;

  async initialise(): Promise<void> {
    const started = performance.now();
    const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
    const files = await FilesetResolver.forVisionTasks(FACE_WASM_PATH);
    this.task = await FaceLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: FACE_MODEL_PATH, delegate: "CPU" }, runningMode: "VIDEO", numFaces: 2,
      minFaceDetectionConfidence: 0.55, minFacePresenceConfidence: 0.55, minTrackingConfidence: 0.55,
      outputFaceBlendshapes: false, outputFacialTransformationMatrixes: false,
    });
    this.modelLoadTime = performance.now() - started;
  }

  detect(video: HTMLVideoElement): LocalFaceResult {
    if (!this.task) throw new Error("The local face detector has not finished loading.");
    const started = performance.now(); const now = Math.max(performance.now(), this.lastTimestamp + 0.01); this.lastTimestamp = now;
    const result = this.task.detectForVideo(video, now); const faceCount = result.faceLandmarks.length;
    const faces = result.faceLandmarks.map((faceLandmarks) => {
      const face = deriveFaceGeometry(faceLandmarks);
      return { boundingBox: face.boundingBox, faceCentre: face.faceCentre, faceSize: face.faceSize };
    });
    const landmarks = faceCount === 1 ? result.faceLandmarks[0] : [];
    const geometry = deriveFaceGeometry(landmarks);
    return { detectorReady: true, faceCount, ...geometry, confidence: null, processingTime: performance.now() - started, faces };
  }

  close(): void { this.task?.close(); this.task = null; }
}

// Compatibility alias for callers compiled against the pre-unification name.
export { LocalFacePerceptionService as LocalFaceLandmarker };

export type FacePresenceKind = "face_detected" | "face_not_detected" | "sustained_face_absence";
export type FacePresenceSignal = { kind: FacePresenceKind; faceCount: number; absenceDurationMs: number };

/** Tracks face-presence transitions without performing identity comparison. */
export class FacePresenceTracker {
  private lastPresent: boolean | null = null;
  private absentSince: number | null = null;
  private sustainedEmitted = false;

  constructor(readonly sustainedAbsenceMs = SUSTAINED_FACE_ABSENCE_MS) {}

  update(faceCount: number, nowMs: number, cameraConnected = true): FacePresenceSignal[] {
    if (!cameraConnected) {
      this.lastPresent = null;
      this.absentSince = null;
      this.sustainedEmitted = false;
      return [];
    }
    const present = faceCount > 0;
    if (present) {
      const changed = this.lastPresent !== true;
      this.lastPresent = true;
      this.absentSince = null;
      this.sustainedEmitted = false;
      return changed ? [{ kind: "face_detected", faceCount, absenceDurationMs: 0 }] : [];
    }
    if (this.lastPresent !== false || this.absentSince == null) {
      this.lastPresent = false;
      this.absentSince = nowMs;
      this.sustainedEmitted = false;
      return [{ kind: "face_not_detected", faceCount: 0, absenceDurationMs: 0 }];
    }
    const absenceDurationMs = Math.max(0, nowMs - this.absentSince);
    if (!this.sustainedEmitted && absenceDurationMs >= this.sustainedAbsenceMs) {
      this.sustainedEmitted = true;
      return [{ kind: "sustained_face_absence", faceCount: 0, absenceDurationMs }];
    }
    return [];
  }
}
