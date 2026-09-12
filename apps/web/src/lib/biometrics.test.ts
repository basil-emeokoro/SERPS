import { afterEach, describe, expect, it, vi } from "vitest";
import { cameraAccessMessage, openIdentityCamera } from "./biometrics";

afterEach(() => vi.unstubAllGlobals());

describe("camera device errors", () => {
  it.each([
    ["NotAllowedError", "Camera access was denied"],
    ["NotFoundError", "No compatible camera was found"],
    ["NotReadableError", "may already be in use"],
    ["OverconstrainedError", "does not satisfy the required video settings"],
    ["AbortError", "no longer available"],
  ])("maps %s to actionable guidance", (name, expected) => {
    expect(cameraAccessMessage(new DOMException("failure", name))).toContain(expected);
  });
  it("uses a safe fallback", () => expect(cameraAccessMessage(new Error("unknown"))).toContain("Unable to access the selected camera"));
  it("opens the selected device once and retains the live stream", async () => {
    const stream = { getTracks: () => [{ stop: vi.fn() }] } as unknown as MediaStream;
    const getUserMedia = vi.fn().mockResolvedValue(stream);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
    const video = { srcObject: null, play: vi.fn().mockResolvedValue(undefined) } as unknown as HTMLVideoElement;
    await expect(openIdentityCamera(video, "integrated-camera")).resolves.toBe(stream);
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(video.srcObject).toBe(stream);
  });
  it("stops the acquired track when video playback fails", async () => {
    const stop = vi.fn();
    const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(stream) } });
    const video = { srcObject: null, play: vi.fn().mockRejectedValue(new DOMException("busy", "NotReadableError")) } as unknown as HTMLVideoElement;
    await expect(openIdentityCamera(video, "integrated-camera")).rejects.toThrow("may already be in use");
    expect(stop).toHaveBeenCalledOnce();
    expect(video.srcObject).toBeNull();
  });
});
