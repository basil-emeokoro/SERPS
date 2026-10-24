import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "./api";
import { attachExaminationPreview, beginReauthentication, canRequestAttempt, fetchReauthentication, reauthenticationMessage, safeExaminationReturn, verifyReauthentication, type ReauthenticationState } from "./reauthentication";
vi.mock("./api", () => ({ apiRequest: vi.fn() }));
const state: ReauthenticationState = { session_id: "SESSION-1", state: "required", required: true };

describe("session-bound identity recovery", () => {
  beforeEach(() => vi.clearAllMocks());
  it("reads requirements without issuing a challenge or starting a session", async () => {
    vi.mocked(apiRequest).mockResolvedValue(state);
    expect(await fetchReauthentication("SESSION-1")).toEqual(state);
    expect(apiRequest).toHaveBeenCalledExactlyOnceWith("/api/v1/identity-assurance/reauthentication/sessions/SESSION-1", { signal: undefined });
  });
  it("binds challenge and observation submission to the originating session", async () => {
    vi.mocked(apiRequest).mockResolvedValue(state);
    await beginReauthentication("SESSION-1");
    const payload = { challenge_token: "test-token", descriptor: [0.5], one_face: true, lighting_score: 0.9, distance_score: 0.9, retry_count: 0 };
    await verifyReauthentication("SESSION-1", payload);
    expect(apiRequest).toHaveBeenNthCalledWith(1, "/api/v1/identity-assurance/reauthentication/sessions/SESSION-1/challenge", { method: "POST" });
    expect(apiRequest).toHaveBeenNthCalledWith(2, "/api/v1/identity-assurance/reauthentication/sessions/SESSION-1/verify", { method: "POST", body: JSON.stringify(payload) });
  });
  it("does not offer consumed manual-review or completed challenges for retry", () => {
    expect(canRequestAttempt({ ...state, state: "manual_review" })).toBe(false);
    expect(canRequestAttempt({ ...state, state: "completed", required: false })).toBe(false);
    expect(canRequestAttempt({ ...state, state: "failed", retry_after: new Date(2000).toISOString() }, 1000)).toBe(false);
    expect(canRequestAttempt({ ...state, state: "failed", retry_after: new Date(2000).toISOString() }, 2000)).toBe(true);
  });
  it("explains terminal recovery without treating manual review as guilt or verification", () => {
    expect(reauthenticationMessage({ ...state, state: "manual_review" })).toContain("human review");
    expect(reauthenticationMessage({ ...state, state: "manual_review" })).toContain("not a misconduct determination");
    expect(reauthenticationMessage({ ...state, state: "released" })).toContain("no biometric verification is claimed");
    expect(reauthenticationMessage({ ...state, state: "expired" })).toContain("fresh bounded attempt");
  });
  it("returns legacy checks only to a valid local examination path", () => {
    expect(safeExaminationReturn("/candidate/examinations/SESSION-1")).toBe("/candidate/examinations/SESSION-1");
    for (const value of [null, "https://evil.invalid", "//evil.invalid", "/candidate/examinations/../admin", "/candidate/examinations/S?next=evil"]) expect(safeExaminationReturn(value)).toBe("/candidate");
  });
});

describe("examination monitoring preservation", () => {
  it("releases only a cloned preview track and preserves the original monitoring stream", async () => {
    const stopMonitoring = vi.fn(); const stopPreview = vi.fn();
    const preview = { getTracks: () => [{ stop: stopPreview }] } as unknown as MediaStream;
    const monitoring = { active: true, clone: () => preview, getTracks: () => [{ stop: stopMonitoring }] } as unknown as MediaStream;
    const video = { srcObject: null, play: vi.fn().mockResolvedValue(undefined) } as unknown as HTMLVideoElement;
    const attached = await attachExaminationPreview(video, monitoring);
    expect(attached).toBe(preview); expect(video.srcObject).toBe(preview);
    attached?.getTracks().forEach((track) => track.stop());
    expect(stopPreview).toHaveBeenCalledOnce(); expect(stopMonitoring).not.toHaveBeenCalled();
  });
  it("releases a failed preview without stopping monitoring", async () => {
    const stopMonitoring = vi.fn(); const stopPreview = vi.fn();
    const monitoring = { active: true, clone: () => ({ getTracks: () => [{ stop: stopPreview }] }), getTracks: () => [{ stop: stopMonitoring }] } as unknown as MediaStream;
    const video = { srcObject: null, play: vi.fn().mockRejectedValue(new Error("play failed")) } as unknown as HTMLVideoElement;
    await expect(attachExaminationPreview(video, monitoring)).rejects.toThrow("play failed");
    expect(stopPreview).toHaveBeenCalledOnce(); expect(stopMonitoring).not.toHaveBeenCalled(); expect(video.srcObject).toBeNull();
  });
});
