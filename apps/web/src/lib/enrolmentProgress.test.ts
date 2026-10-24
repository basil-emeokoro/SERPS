import { describe, expect, it } from "vitest";
import { ENROLMENT_PROGRESS_KEY, readEnrolmentProgress, writeEnrolmentProgress } from "./enrolmentProgress";

const poses = ["forward", "left", "right", "up", "down", "centre_confirmation"];
const capture = (pose: string) => ({ pose, descriptor: [0.5], one_face: true, pose_validated: true, lighting_score: 0.8, distance_score: 0.8, confidence: 0.8 });

describe("enrolment progress", () => {
  it("restores an ordered capture prefix", () => {
    const values = new Map<string, string>();
    const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => values.set(key, value) };
    writeEnrolmentProgress(storage, { subject: "candidate@example.org", captures: [capture("forward"), capture("left")], liveness: [], actions: ["turn_left"], retryCount: 1 });
    expect(readEnrolmentProgress(storage, "candidate@example.org", poses, ["turn_left"])?.captures).toHaveLength(2);
  });

  it("rejects an out-of-order checkpoint and resets liveness for a changed challenge", () => {
    expect(readEnrolmentProgress({ getItem: () => JSON.stringify({ subject: "candidate@example.org", captures: [capture("left")], liveness: [], actions: [], retryCount: 0 }) }, "candidate@example.org", poses, [])).toBeNull();
    const changed = { getItem: (key: string) => key === ENROLMENT_PROGRESS_KEY ? JSON.stringify({ subject: "candidate@example.org", captures: poses.map(capture), liveness: [{ action: "turn_left", completed: true, confidence: .8, timestamp: new Date().toISOString() }], actions: ["turn_left"], retryCount: 0 }) : null };
    expect(readEnrolmentProgress(changed, "candidate@example.org", poses, ["turn_left"])?.liveness).toEqual([]);
  });

  it("truncates legacy captures at the first backend-ineligible observation", () => {
    const lowQuality = { ...capture("left"), confidence: 0.52 };
    const storage = { getItem: () => JSON.stringify({ subject: "candidate@example.org", captures: [capture("forward"), lowQuality, capture("right")], liveness: [], actions: [], retryCount: 0 }) };
    expect(readEnrolmentProgress(storage, "candidate@example.org", poses, [])?.captures.map((item) => item.pose)).toEqual(["forward"]);
  });

  it("does not restore another account's derived observations", () => {
    const storage = { getItem: () => JSON.stringify({ subject: "first@example.org", captures: [capture("forward")], liveness: [], actions: [], retryCount: 0 }) };
    expect(readEnrolmentProgress(storage, "second@example.org", poses, [])).toBeNull();
  });
});
