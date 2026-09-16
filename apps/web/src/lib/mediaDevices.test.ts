import { afterEach, describe, expect, it, vi } from "vitest";
import { classifyMediaError, discoverVideoDevices } from "./mediaDevices";

afterEach(() => vi.unstubAllGlobals());

function device(kind: MediaDeviceKind, id: string): MediaDeviceInfo { return { kind, deviceId: id, groupId: "group", label: id, toJSON: () => ({}) }; }

describe("candidate camera discovery", () => {
  it("enumerates while the permission stream is live and releases it afterwards", async () => {
    let stopped = false;
    const stream = { getTracks: () => [{ stop: () => { stopped = true; } }] } as unknown as MediaStream;
    const enumerateDevices = vi.fn().mockImplementation(async () => { expect(stopped).toBe(false); return [device("videoinput", "integrated"), device("audioinput", "mic")]; });
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(stream), enumerateDevices } });
    const result = await discoverVideoDevices();
    expect(result.devices.map((item) => item.deviceId)).toEqual(["integrated"]);
    expect(stopped).toBe(true);
  });

  it("reports empty enumeration as a media failure and still releases the stream", async () => {
    const stop = vi.fn();
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] }), enumerateDevices: vi.fn().mockResolvedValue([]) } });
    await expect(discoverVideoDevices()).rejects.toEqual(expect.objectContaining({ kind: "no_device" }));
    expect(stop).toHaveBeenCalledOnce();
  });

  it("classifies the Edge video-source timeout as a busy acquisition", () => {
    expect(classifyMediaError(new DOMException("Timeout starting video source", "NotReadableError"))).toEqual(expect.objectContaining({ kind: "device_busy" }));
  });
});
