import { describe, expect, it } from "vitest";
import { ENROLMENT_PROGRESS_KEY, readEnrolmentProgress, writeEnrolmentProgress } from "./enrolmentProgress";

const poses = ["forward", "left", "right", "up", "down", "centre_confirmation"];
const capture = (pose: string) => ({ pose, descriptor: [0.5], one_face: true, pose_validated: true, lighting_score: 0.8, distance_score: 0.8, confidence: 0.8 });

describe("enrolment progress", () => {
  it("restores an ordered capture prefix", () => {
    const values = new Map<string, string>();
    const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => values.set(key, value) };
    writeEnrolmentProgress(storage, { captures: [capture("forward"), capture("left")], liveness: [], actions: ["turn_left"], retryCount: 1 });
    expect(readEnrolmentProgress(storage, poses, ["turn_left"])?.captures).toHaveLength(2);
  });

  it("rejects an out-of-order checkpoint and resets liveness for a changed challenge", () => {
    expect(readEnrolmentProgress({ getItem: () => JSON.stringify({ captures: [capture("left")], liveness: [], actions: [], retryCount: 0 }) }, poses, [])).toBeNull();
    const changed = { getItem: (key: string) => key === ENROLMENT_PROGRESS_KEY ? JSON.stringify({ captures: [capture("forward")], liveness: [{ action: "turn_left", completed: true, confidence: .8, timestamp: new Date().toISOString() }], actions: ["turn_left"], retryCount: 0 }) : null };
    expect(readEnrolmentProgress(changed, poses, ["turn_right"])?.liveness).toEqual([]);
  });
});
