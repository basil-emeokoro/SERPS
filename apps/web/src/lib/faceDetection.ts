import type { NormalizedLandmark } from "@mediapipe/tasks-vision";

export type FaceBoundingBox = { x: number; y: number; width: number; height: number };
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
};

type FaceLandmarkerInstance = import("@mediapipe/tasks-vision").FaceLandmarker;

const WASM_PATH = "/mediapipe/wasm";
const MODEL_PATH = "/mediapipe/models/face_landmarker.task";

function clamp(value: number): number { return Math.max(-1, Math.min(1, value)); }

export function deriveFaceGeometry(landmarks: NormalizedLandmark[]): Omit<LocalFaceResult, "detectorReady" | "faceCount" | "processingTime" | "confidence"> {
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

export class LocalFaceLandmarker {
  private task: FaceLandmarkerInstance | null = null;
  private lastTimestamp = 0;
  modelLoadTime = 0;

  async initialise(): Promise<void> {
    const started = performance.now();
    const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
    const files = await FilesetResolver.forVisionTasks(WASM_PATH);
    this.task = await FaceLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: MODEL_PATH, delegate: "CPU" }, runningMode: "VIDEO", numFaces: 2,
      minFaceDetectionConfidence: 0.55, minFacePresenceConfidence: 0.55, minTrackingConfidence: 0.55,
      outputFaceBlendshapes: false, outputFacialTransformationMatrixes: false,
    });
    this.modelLoadTime = performance.now() - started;
  }

  detect(video: HTMLVideoElement): LocalFaceResult {
    if (!this.task) throw new Error("The local face detector has not finished loading.");
    const started = performance.now(); const now = Math.max(performance.now(), this.lastTimestamp + 0.01); this.lastTimestamp = now;
    const result = this.task.detectForVideo(video, now); const faceCount = result.faceLandmarks.length;
    const landmarks = faceCount === 1 ? result.faceLandmarks[0] : [];
    const geometry = deriveFaceGeometry(landmarks);
    return { detectorReady: true, faceCount, ...geometry, confidence: null, processingTime: performance.now() - started };
  }

  close(): void { this.task?.close(); this.task = null; }
}
