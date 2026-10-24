import { afterEach, expect, it, vi } from "vitest";
import { LocalFacePerceptionService } from "./faceDetection";
import { LocalObjectDetector } from "./objectDetection";
const mocks = vi.hoisted(() => ({ create: vi.fn() }));
vi.mock("@mediapipe/tasks-vision", () => ({ FilesetResolver: { forVisionTasks: async () => ({}) },
  FaceLandmarker: { createFromOptions: mocks.create }, ObjectDetector: { createFromOptions: mocks.create } }));
afterEach(() => vi.clearAllMocks());
it.each([LocalFacePerceptionService, LocalObjectDetector])("releases late initialisation and never creates duplicate instances: %s", async Type => {
  const close = vi.fn(); let resolve!: (task: { close: typeof close }) => void;
  mocks.create.mockReturnValue(new Promise(r => { resolve = r; }));
  const detector = new Type(); const first = detector.initialise(); const second = detector.initialise();
  await vi.waitFor(() => expect(mocks.create).toHaveBeenCalledTimes(1));
  detector.close(); resolve({ close }); await Promise.all([first, second]);
  expect(close).toHaveBeenCalledTimes(1); detector.close(); expect(close).toHaveBeenCalledTimes(1);
  await expect(detector.initialise()).rejects.toThrow("released");
});
