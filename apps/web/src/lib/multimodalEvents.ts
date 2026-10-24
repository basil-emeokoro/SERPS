import { AUDIO_MONITOR_NAME, AUDIO_MONITOR_VERSION, type AudioActivitySignal } from "./audioMonitoring";
import { OBJECT_MODEL_NAME, OBJECT_MODEL_VERSION, type ObjectDetectionSnapshot } from "./objectDetection";
import { FACE_PERCEPTION_NAME, FACE_PERCEPTION_VERSION, type FacePresenceSignal, type LocalFaceResult } from "./faceDetection";

export type CameraRole = "primary" | "secondary";
export type ProctoringMode = "A" | "B" | "C";

export function objectRolesForMode(mode: ProctoringMode): CameraRole[] {
  return mode === "B" ? ["primary", "secondary"] : ["primary"];
}

export type EvidenceDraft = {
  eventType: string;
  description: string;
  cameraId?: CameraRole;
  confidence: number;
  riskWeight: number;
  metadata: Record<string, unknown>;
};

export class DuplicateEventGate {
  private lastEmitted = new Map<string, number>();
  constructor(private readonly cooldownMs = 10000) {}

  allow(key: string, nowMs: number): boolean {
    const previous = this.lastEmitted.get(key);
    if (previous != null && nowMs - previous < this.cooldownMs) return false;
    this.lastEmitted.set(key, nowMs);
    return true;
  }
}

export function objectEvidence(snapshot: ObjectDetectionSnapshot, cameraRole: CameraRole): EvidenceDraft[] {
  const common = {
    source: "local_browser_object_detector",
    camera_role: cameraRole,
    model_name: snapshot.modelName,
    model_version: snapshot.modelVersion,
    threshold: snapshot.threshold,
    processing_time_ms: Number(snapshot.processingTime.toFixed(2)),
    raw_video_stored: false,
  };
  const drafts: EvidenceDraft[] = [];
  if (snapshot.personCount === 1) {
    const confidence = Math.max(...snapshot.detections.filter((item) => item.detectedClass === "person").map((item) => item.confidence));
    drafts.push({ eventType: "person_detected", description: `One person was detected by the local object detector on the ${cameraRole} camera.`, cameraId: cameraRole, confidence, riskWeight: 0, metadata: { ...common, detected_class: "person", object_count: 1 } });
  }
  if (snapshot.personCount > 1) {
    const confidence = Math.max(...snapshot.detections.filter((item) => item.detectedClass === "person").map((item) => item.confidence));
    drafts.push({ eventType: "multiple_persons_detected", description: `${snapshot.personCount} persons were detected by the local object detector on the ${cameraRole} camera.`, cameraId: cameraRole, confidence, riskWeight: 0.55, metadata: { ...common, detected_class: "person", object_count: snapshot.personCount } });
  }
  if (snapshot.mobilePhoneCount > 0) {
    const confidence = Math.max(...snapshot.detections.filter((item) => item.detectedClass === "cell phone").map((item) => item.confidence));
    drafts.push({ eventType: "mobile_phone_detected", description: `${snapshot.mobilePhoneCount} mobile phone object${snapshot.mobilePhoneCount === 1 ? "" : "s"} detected on the ${cameraRole} camera.`, cameraId: cameraRole, confidence, riskWeight: 0.65, metadata: { ...common, detected_class: "cell phone", object_count: snapshot.mobilePhoneCount } });
  }
  return drafts;
}

export function detectorUnavailableEvidence(cameraRole: CameraRole, reason: string): EvidenceDraft {
  return {
    eventType: "object_detector_unavailable",
    description: `The local object detector was unavailable for the ${cameraRole} camera: ${reason}`,
    cameraId: cameraRole,
    confidence: 1,
    riskWeight: 0,
    metadata: { source: "local_browser_object_detector", camera_role: cameraRole, model_name: OBJECT_MODEL_NAME, model_version: OBJECT_MODEL_VERSION, unavailable_reason: reason, raw_video_stored: false },
  };
}

export function audioEvidence(signal: AudioActivitySignal): EvidenceDraft {
  return {
    eventType: signal.kind,
    description: signal.kind === "sustained_audio_activity"
      ? `Audio activity remained above the configured threshold for ${Math.round(signal.durationMs)} ms.`
      : `Audio activity exceeded the configured threshold for ${Math.round(signal.durationMs)} ms.`,
    confidence: Math.max(0, Math.min(signal.normalizedLevel / Math.max(signal.threshold, 0.001), 1)),
    riskWeight: signal.kind === "sustained_audio_activity" ? 0.35 : 0.05,
    metadata: {
      source: "local_browser_audio_monitor",
      normalized_level: Number(signal.normalizedLevel.toFixed(5)),
      threshold: signal.threshold,
      duration_ms: Math.round(signal.durationMs),
      recurrence_count: signal.recurrenceCount,
      detector_name: AUDIO_MONITOR_NAME,
      detector_version: AUDIO_MONITOR_VERSION,
      correlation_window_seconds: 60,
      raw_audio_stored: false,
    },
  };
}

export function facePresenceEvidence(signal: FacePresenceSignal, snapshot: LocalFaceResult): EvidenceDraft {
  const primaryFace = snapshot.faces[0] ?? null;
  const descriptions: Record<FacePresenceSignal["kind"], string> = {
    face_detected: `${snapshot.faceCount} face${snapshot.faceCount === 1 ? "" : "s"} detected in the primary candidate-facing view.`,
    face_not_detected: "No face was detected in the connected primary candidate-facing view.",
    sustained_face_absence: `No face was detected continuously for ${Math.round(signal.absenceDurationMs)} ms in the connected primary view.`,
  };
  return {
    eventType: signal.kind,
    description: descriptions[signal.kind],
    cameraId: "primary",
    // MediaPipe Tasks does not expose a calibrated per-face confidence here.
    // Keep the field truthful instead of inventing a score.
    confidence: snapshot.confidence ?? 0,
    riskWeight: signal.kind === "face_detected" ? 0 : signal.kind === "sustained_face_absence" ? 0.5 : 0.15,
    metadata: {
      source: "local_mediapipe_face_perception",
      detector_name: FACE_PERCEPTION_NAME,
      detector_version: FACE_PERCEPTION_VERSION,
      purpose: "face_presence_monitoring",
      identity_matching_performed: false,
      face_count: snapshot.faceCount,
      bounding_box: primaryFace?.boundingBox ?? null,
      face_centre: primaryFace?.faceCentre ?? null,
      face_size: primaryFace?.faceSize ?? null,
      processing_time_ms: Number(snapshot.processingTime.toFixed(2)),
      detector_confidence_available: snapshot.confidence != null,
      absence_duration_ms: Math.round(signal.absenceDurationMs),
      raw_video_stored: false,
    },
  };
}

export function faceDetectorUnavailableEvidence(reason: string): EvidenceDraft {
  return {
    eventType: "face_detector_unavailable",
    description: `Local MediaPipe face monitoring is unavailable; other configured evidence sources remain active. Reason: ${reason}`,
    cameraId: "primary",
    confidence: 1,
    riskWeight: 0,
    metadata: {
      source: "local_mediapipe_face_perception",
      detector_name: FACE_PERCEPTION_NAME,
      detector_version: FACE_PERCEPTION_VERSION,
      purpose: "face_presence_monitoring",
      identity_matching_performed: false,
      unavailable_reason: reason,
      raw_video_stored: false,
    },
  };
}
