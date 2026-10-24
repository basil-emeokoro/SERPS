import { beforeEach, describe, expect, it, vi } from "vitest";
import { FACE_MODEL_PATH, FACE_WASM_PATH, FacePresenceTracker, LocalFacePerceptionService } from "./faceDetection";
import { faceDetectorUnavailableEvidence, facePresenceEvidence } from "./multimodalEvents";

const createFromOptions = vi.fn();
const forVisionTasks = vi.fn();

vi.mock("@mediapipe/tasks-vision", () => ({
  FilesetResolver: { forVisionTasks },
  FaceLandmarker: { createFromOptions },
}));

function landmarks(offset = 0) {
  return Array.from({ length: 478 }, (_, index) => ({
    x: 0.35 + ((index % 20) / 100) + offset,
    y: 0.30 + ((index % 25) / 100),
    z: 0,
    visibility: 1,
  }));
}

describe("shared local MediaPipe face perception", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    forVisionTasks.mockResolvedValue({ wasm: "local" });
  });

  it("initialises the locally bundled WASM and model for two-face perception", async () => {
    createFromOptions.mockResolvedValue({ detectForVideo: vi.fn(() => ({ faceLandmarks: [] })), close: vi.fn() });
    const detector = new LocalFacePerceptionService();
    await detector.initialise();
    expect(forVisionTasks).toHaveBeenCalledWith(FACE_WASM_PATH);
    expect(createFromOptions).toHaveBeenCalledWith({ wasm: "local" }, expect.objectContaining({
      baseOptions: expect.objectContaining({ modelAssetPath: FACE_MODEL_PATH }),
      runningMode: "VIDEO",
      numFaces: 2,
    }));
  });

  it("reports face presence, reliable count and bounding metadata without identity matching", async () => {
    createFromOptions.mockResolvedValue({ detectForVideo: vi.fn(() => ({ faceLandmarks: [landmarks(), landmarks(0.1)] })), close: vi.fn() });
    const detector = new LocalFacePerceptionService();
    await detector.initialise();
    const snapshot = detector.detect({} as HTMLVideoElement);
    expect(snapshot.faceCount).toBe(2);
    expect(snapshot.faces).toHaveLength(2);
    expect(snapshot.faces[0].boundingBox).not.toBeNull();
  });

  it("emits transition, sustained absence and recovery signals", () => {
    const tracker = new FacePresenceTracker(3000);
    expect(tracker.update(1, 0).map((item) => item.kind)).toEqual(["face_detected"]);
    expect(tracker.update(0, 1000).map((item) => item.kind)).toEqual(["face_not_detected"]);
    expect(tracker.update(0, 2500)).toEqual([]);
    expect(tracker.update(0, 4000).map((item) => item.kind)).toEqual(["sustained_face_absence"]);
    expect(tracker.update(1, 4500).map((item) => item.kind)).toEqual(["face_detected"]);
  });

  it("distinguishes camera disconnection from face absence", () => {
    const tracker = new FacePresenceTracker(1000);
    expect(tracker.update(0, 0, false)).toEqual([]);
    expect(tracker.update(0, 5000, false)).toEqual([]);
    expect(tracker.update(0, 6000, true).map((item) => item.kind)).toEqual(["face_not_detected"]);
  });

  it("creates presence evidence and a zero-risk degraded-mode event", () => {
    const snapshot = {
      detectorReady: true, faceCount: 0, boundingBox: null, landmarks: [], faceCentre: null, faceSize: null,
      yawEstimate: null, pitchEstimate: null, rollEstimate: null, confidence: null, processingTime: 12, faces: [],
    };
    const absent = facePresenceEvidence({ kind: "face_not_detected", faceCount: 0, absenceDurationMs: 0 }, snapshot);
    expect(absent.metadata).toMatchObject({ identity_matching_performed: false, face_count: 0, raw_video_stored: false });
    const unavailable = faceDetectorUnavailableEvidence("model missing");
    expect(unavailable.eventType).toBe("face_detector_unavailable");
    expect(unavailable.riskWeight).toBe(0);
  });
});
