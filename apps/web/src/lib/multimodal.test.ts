import { beforeEach, describe, expect, it, vi } from "vitest";
import { AudioActivityTracker } from "./audioMonitoring";
import { audioEvidence, detectorUnavailableEvidence, DuplicateEventGate, objectEvidence, objectRolesForMode } from "./multimodalEvents";
import { LocalObjectDetector, OBJECT_MODEL_PATH, type ObjectDetectionSnapshot } from "./objectDetection";

const createFromOptions = vi.fn();
const forVisionTasks = vi.fn();

vi.mock("@mediapipe/tasks-vision", () => ({
  FilesetResolver: { forVisionTasks },
  ObjectDetector: { createFromOptions },
}));

function snapshot(personCount: number, mobilePhoneCount: number): ObjectDetectionSnapshot {
  return {
    detectorReady: true,
    modelName: "EfficientDet-Lite0 (COCO)",
    modelVersion: "float32/1",
    threshold: 0.55,
    personCount,
    mobilePhoneCount,
    detections: [
      ...Array.from({ length: personCount }, () => ({ detectedClass: "person" as const, confidence: 0.91, boundingBox: null })),
      ...Array.from({ length: mobilePhoneCount }, () => ({ detectedClass: "cell phone" as const, confidence: 0.87, boundingBox: null })),
    ],
    processingTime: 22,
  };
}

describe("local object detector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    forVisionTasks.mockResolvedValue({ wasm: "local" });
  });

  it("loads the local EfficientDet model with bounded classes and threshold", async () => {
    createFromOptions.mockResolvedValue({ detectForVideo: vi.fn(() => ({ detections: [] })), close: vi.fn() });
    const detector = new LocalObjectDetector(0.6);
    await detector.initialise();
    expect(forVisionTasks).toHaveBeenCalledWith("/mediapipe/wasm");
    expect(createFromOptions).toHaveBeenCalledWith({ wasm: "local" }, expect.objectContaining({
      baseOptions: expect.objectContaining({ modelAssetPath: OBJECT_MODEL_PATH }),
      runningMode: "VIDEO",
      scoreThreshold: 0.6,
      categoryAllowlist: ["person", "cell phone"],
    }));
  });

  it("maps recognised person, multiple-person and mobile-phone findings into genuine event drafts", () => {
    expect(objectEvidence(snapshot(1, 0), "primary").map((item) => item.eventType)).toEqual(["person_detected"]);
    expect(objectEvidence(snapshot(2, 1), "secondary").map((item) => item.eventType)).toEqual(["multiple_persons_detected", "mobile_phone_detected"]);
    expect(objectEvidence(snapshot(2, 1), "secondary")[0].metadata).toMatchObject({ detected_class: "person", object_count: 2, raw_video_stored: false });
  });

  it("rejects below-threshold detector categories even when a fixture returns them", async () => {
    createFromOptions.mockResolvedValue({
      detectForVideo: vi.fn(() => ({ detections: [{ categories: [{ categoryName: "cell phone", score: 0.2 }], boundingBox: null }] })),
      close: vi.fn(),
    });
    const detector = new LocalObjectDetector(0.55);
    await detector.initialise();
    const result = detector.detect({} as HTMLVideoElement);
    expect(result.mobilePhoneCount).toBe(0);
    expect(result.detections).toEqual([]);
  });

  it("reports detector-unavailable state without fabricating a detection", () => {
    const event = detectorUnavailableEvidence("primary", "model missing");
    expect(event.eventType).toBe("object_detector_unavailable");
    expect(event.riskWeight).toBe(0);
    expect(event.metadata).toMatchObject({ unavailable_reason: "model missing", raw_video_stored: false });
  });

  it("suppresses duplicate events inside the configured cooldown", () => {
    const gate = new DuplicateEventGate(1000);
    expect(gate.allow("phone:primary", 1000)).toBe(true);
    expect(gate.allow("phone:primary", 1500)).toBe(false);
    expect(gate.allow("phone:primary", 2000)).toBe(true);
  });
});

describe("privacy-safe audio activity", () => {
  it("ignores below-threshold samples and emits bounded activity then sustained activity", () => {
    const tracker = new AudioActivityTracker(0.1, 500, 2000, 1000);
    expect(tracker.update(0.05, 0)).toEqual([]);
    expect(tracker.update(0.2, 100)).toEqual([]);
    expect(tracker.update(0.2, 600).map((item) => item.kind)).toEqual(["audio_activity_detected"]);
    expect(tracker.update(0.2, 2100).map((item) => item.kind)).toEqual(["sustained_audio_activity"]);
  });

  it("creates privacy-safe metadata without raw audio", () => {
    const event = audioEvidence({ kind: "sustained_audio_activity", normalizedLevel: 0.2, threshold: 0.08, durationMs: 2600, recurrenceCount: 2 });
    expect(event.metadata).toMatchObject({ duration_ms: 2600, recurrence_count: 2, raw_audio_stored: false });
    expect(event.metadata).not.toHaveProperty("audio_samples");
  });
});

describe("proctoring modes", () => {
  it.each([["A", ["primary"]], ["B", ["primary", "secondary"]], ["C", ["primary"]]] as const)("uses the expected object camera roles in Mode %s", (mode, roles) => {
    expect(objectRolesForMode(mode)).toEqual(roles);
  });
});
