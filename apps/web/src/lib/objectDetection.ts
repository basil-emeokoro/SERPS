export const OBJECT_MODEL_NAME = "EfficientDet-Lite0 (COCO)";
export const OBJECT_MODEL_VERSION = "float32/1";
export const OBJECT_MODEL_PATH = "/mediapipe/models/efficientdet_lite0.tflite";
export const OBJECT_SAMPLE_INTERVAL_MS = 1500;
export const DEFAULT_OBJECT_CONFIDENCE_THRESHOLD = 0.55;

export type MonitoredObjectClass = "person" | "cell phone";

export type ObjectFinding = {
  detectedClass: MonitoredObjectClass;
  confidence: number;
  boundingBox: { x: number; y: number; width: number; height: number } | null;
};

export type ObjectDetectionSnapshot = {
  detectorReady: boolean;
  modelName: string;
  modelVersion: string;
  threshold: number;
  personCount: number;
  mobilePhoneCount: number;
  detections: ObjectFinding[];
  processingTime: number;
};

type ObjectDetectorInstance = import("@mediapipe/tasks-vision").ObjectDetector;

function configuredThreshold(): number {
  const candidate = Number(process.env.NEXT_PUBLIC_OBJECT_DETECTION_THRESHOLD ?? DEFAULT_OBJECT_CONFIDENCE_THRESHOLD);
  return Number.isFinite(candidate) && candidate >= 0.1 && candidate <= 0.95
    ? candidate
    : DEFAULT_OBJECT_CONFIDENCE_THRESHOLD;
}

export class LocalObjectDetector {
  private task: ObjectDetectorInstance | null = null;
  private lastTimestamp = 0;
  readonly threshold: number;
  modelLoadTime = 0;

  constructor(threshold = configuredThreshold()) {
    this.threshold = threshold;
  }

  async initialise(): Promise<void> {
    const started = performance.now();
    const { FilesetResolver, ObjectDetector } = await import("@mediapipe/tasks-vision");
    const files = await FilesetResolver.forVisionTasks("/mediapipe/wasm");
    this.task = await ObjectDetector.createFromOptions(files, {
      baseOptions: { modelAssetPath: OBJECT_MODEL_PATH, delegate: "CPU" },
      runningMode: "VIDEO",
      maxResults: 8,
      scoreThreshold: this.threshold,
      categoryAllowlist: ["person", "cell phone"],
    });
    this.modelLoadTime = performance.now() - started;
  }

  detect(video: HTMLVideoElement): ObjectDetectionSnapshot {
    if (!this.task) throw new Error("The local object detector has not finished loading.");
    const started = performance.now();
    const timestamp = Math.max(performance.now(), this.lastTimestamp + 0.01);
    this.lastTimestamp = timestamp;
    const result = this.task.detectForVideo(video, timestamp);
    const detections: ObjectFinding[] = [];
    for (const detection of result.detections) {
      const best = [...detection.categories].sort((left, right) => right.score - left.score)[0];
      const category = best?.categoryName?.toLowerCase();
      if ((category !== "person" && category !== "cell phone") || best.score < this.threshold) continue;
      const box = detection.boundingBox;
      detections.push({
        detectedClass: category,
        confidence: Number(best.score.toFixed(4)),
        boundingBox: box
          ? { x: box.originX, y: box.originY, width: box.width, height: box.height }
          : null,
      });
    }
    return {
      detectorReady: true,
      modelName: OBJECT_MODEL_NAME,
      modelVersion: OBJECT_MODEL_VERSION,
      threshold: this.threshold,
      personCount: detections.filter((item) => item.detectedClass === "person").length,
      mobilePhoneCount: detections.filter((item) => item.detectedClass === "cell phone").length,
      detections,
      processingTime: performance.now() - started,
    };
  }

  close(): void {
    this.task?.close();
    this.task = null;
  }
}
