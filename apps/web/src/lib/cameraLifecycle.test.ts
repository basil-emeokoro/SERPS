// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { AssignedCamera, FreshCameraFrame } from "./cameraLifecycle";

function source() {
  const track = Object.assign(new EventTarget(), { readyState: "live", muted: false, stop: vi.fn(() => { track.readyState = "ended"; }) });
  const stream = Object.assign(new EventTarget(), { get active() { return track.readyState === "live"; }, getTracks: () => [track], getVideoTracks: () => [track] });
  return { track, stream: stream as unknown as MediaStream };
}
function video() { return { srcObject: null, play: vi.fn().mockResolvedValue(undefined), paused: false, readyState: 4, videoWidth: 640, videoHeight: 480, currentTime: 1 } as unknown as HTMLVideoElement; }

describe("assigned camera ownership", () => {
  it("retains a muted stream and recovers on unmute without reacquisition or stop", async () => {
    const { track, stream } = source(); const v = video(); const changed = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue(stream);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
    const camera = new AssignedCamera("C1", () => v, changed);
    await camera.connect();
    track.muted = true; track.dispatchEvent(new Event("mute"));
    expect(changed.mock.calls.at(-1)?.[0]).toBe("muted");
    expect(camera.stream).toBe(stream); expect(v.srcObject).toBe(stream);
    await camera.connect();
    track.muted = false; track.dispatchEvent(new Event("unmute"));
    expect(changed.mock.calls.at(-1)).toEqual(["connected", "live track available", true]);
    expect(getUserMedia).toHaveBeenCalledTimes(1); expect(track.stop).not.toHaveBeenCalled();
    camera.close(); expect(track.stop).toHaveBeenCalledTimes(1);
    track.dispatchEvent(new Event("ended")); expect(changed).toHaveBeenCalledTimes(3);
  });
  it("recognises ended tracks, replaces only the failed source and ignores retired events", async () => {
    const a = source(), b = source(), changed = vi.fn(), v = video();
    const getUserMedia = vi.fn().mockResolvedValueOnce(a.stream).mockResolvedValueOnce(b.stream);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
    const camera = new AssignedCamera("C1", () => v, changed);
    await camera.connect(); a.track.readyState = "ended"; a.track.dispatchEvent(new Event("ended"));
    expect(changed.mock.calls.at(-1)?.[1]).toBe("track ended");
    await camera.connect(); expect(camera.stream).toBe(b.stream);
    const count = changed.mock.calls.length; a.track.dispatchEvent(new Event("mute"));
    expect(changed).toHaveBeenCalledTimes(count); camera.close();
  });
  it("stops late acquisition after unmount and deduplicates pending acquisition", async () => {
    const a = source(); let resolve!: (s: MediaStream) => void;
    const getUserMedia = vi.fn(() => new Promise<MediaStream>(r => { resolve = r; }));
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
    const changed = vi.fn(); const camera = new AssignedCamera("C1", video, changed);
    const pending = camera.connect(); expect(camera.connect()).toBe(pending);
    camera.close(); resolve(a.stream); await pending;
    expect(a.track.stop).toHaveBeenCalledTimes(1); expect(changed).not.toHaveBeenCalled();
  });
  it("rejects lost, muted, repeated and frozen frames without fabricating a detection", () => {
    const a = source(), v = video(), frames = new FreshCameraFrame(); v.srcObject = a.stream;
    expect(frames.available(a.stream, v)).toBe(true);
    expect(frames.available(a.stream, v)).toBe(false);
    v.currentTime = 2; a.track.muted = true; expect(frames.available(a.stream, v)).toBe(false);
    a.track.muted = false; expect(frames.available(a.stream, v)).toBe(true);
    a.track.readyState = "ended"; v.currentTime = 3; expect(frames.available(a.stream, v)).toBe(false);
  });
});

it("rejects unchanged decoded-frame counts even when the media clock advances", () => {
  const a = source(), v = video(), frames = new FreshCameraFrame(); v.srcObject = a.stream;
  v.getVideoPlaybackQuality = () => ({ totalVideoFrames: 10 }) as VideoPlaybackQuality;
  expect(frames.available(a.stream, v)).toBe(true);
  v.currentTime = 5; expect(frames.available(a.stream, v)).toBe(false);
  v.getVideoPlaybackQuality = () => ({ totalVideoFrames: 11 }) as VideoPlaybackQuality;
  expect(frames.available(a.stream, v)).toBe(true);
});
