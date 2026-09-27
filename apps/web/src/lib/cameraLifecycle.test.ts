// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { AssignedCamera, FreshCameraFrame, CameraFrameSampler } from "./cameraLifecycle";

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


it("captures from a healthy track despite frozen preview counters and closes each snapshot", async () => {
  const a = source(), v = video(), frames = new CameraFrameSampler(), consume = vi.fn(); v.srcObject = a.stream;
  const close = vi.fn(), grabFrame = vi.fn(async () => ({ width: 640, height: 480, close }));
  vi.stubGlobal("ImageCapture", class { grabFrame = grabFrame; });
  try {
    expect(await frames.sample(a.stream, v, consume)).toBe(true);
    expect(await frames.sample(a.stream, v, consume)).toBe(true);
    expect(consume).toHaveBeenCalledTimes(2); expect(close).toHaveBeenCalledTimes(2);
    a.track.muted = true; expect(await frames.sample(a.stream, v, consume)).toBe(false);
    expect(grabFrame).toHaveBeenCalledTimes(2); expect(a.track.stop).not.toHaveBeenCalled();
  } finally { frames.close(); vi.unstubAllGlobals(); }
});

it("bounds stalled captures, rejects late frames and does not overlap or leak snapshots", async () => {
  vi.useFakeTimers();
  const a = source(), frames = new CameraFrameSampler(), consume = vi.fn(), close = vi.fn();
  let resolve!: (frame: ImageBitmap) => void;
  const grabFrame = vi.fn(() => new Promise<ImageBitmap>(r => { resolve = r; }));
  vi.stubGlobal("ImageCapture", class { grabFrame = grabFrame; });
  try {
    const pending = frames.sample(a.stream, video(), consume);
    await vi.advanceTimersByTimeAsync(1500); expect(await pending).toBe(false);
    expect(await frames.sample(a.stream, video(), consume)).toBe(false);
    expect(grabFrame).toHaveBeenCalledTimes(1);
    resolve({ width: 640, height: 480, close } as unknown as ImageBitmap);
    await vi.advanceTimersByTimeAsync(0);
    expect(consume).not.toHaveBeenCalled(); expect(close).toHaveBeenCalledTimes(1);
    const next = frames.sample(a.stream, video(), consume); await vi.advanceTimersByTimeAsync(0);
    frames.close(); resolve({ width: 640, height: 480, close } as unknown as ImageBitmap);
    expect(await next).toBe(false); expect(close).toHaveBeenCalledTimes(2);
    expect(a.track.stop).not.toHaveBeenCalled();
  } finally { frames.close(); vi.unstubAllGlobals(); vi.useRealTimers(); }
});

it("closes frames even when inference fails and allows the next sample", async () => {
  const a = source(), frames = new CameraFrameSampler(), close = vi.fn();
  vi.stubGlobal("ImageCapture", class { async grabFrame() { return { width: 640, height: 480, close }; } });
  try {
    await expect(frames.sample(a.stream, video(), () => { throw new Error("inference"); })).rejects.toThrow("inference");
    expect(close).toHaveBeenCalledTimes(1);
    expect(await frames.sample(a.stream, video(), vi.fn())).toBe(true);
  } finally { frames.close(); vi.unstubAllGlobals(); }
});
