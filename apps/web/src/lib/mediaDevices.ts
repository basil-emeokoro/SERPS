export type MediaFailureKind = "permission_denied" | "no_device" | "device_busy" | "acquisition_timeout" | "playback_failure" | "device_disconnected" | "unsupported" | "unknown";

export class MediaLifecycleError extends Error {
  constructor(public readonly kind: MediaFailureKind, message: string, options?: ErrorOptions) { super(message, options); }
}

export function stopMediaStream(stream: MediaStream | null | undefined): void {
  stream?.getTracks().forEach((track) => track.stop());
}

export function classifyMediaError(error: unknown, operation: "acquisition" | "playback" = "acquisition"): MediaLifecycleError {
  if (error instanceof MediaLifecycleError) return error;
  const name = error instanceof DOMException ? error.name : error instanceof Error ? error.name : "";
  const message = error instanceof Error ? error.message.toLowerCase() : "";
  if (name === "NotAllowedError" || name === "SecurityError") return new MediaLifecycleError("permission_denied", "Camera permission was denied. Allow camera access in Microsoft Edge and retry.", { cause: error });
  if (name === "NotFoundError" || name === "DevicesNotFoundError") return new MediaLifecycleError("no_device", "No video-input device was found. Connect a camera and retry discovery.", { cause: error });
  if (name === "NotReadableError" || name === "TrackStartError" || message.includes("starting video source")) return new MediaLifecycleError("device_busy", "The camera could not start and may still be in use. Close other camera sessions, then retry discovery.", { cause: error });
  if (name === "AbortError" || name === "InvalidStateError") return new MediaLifecycleError("device_disconnected", "The camera became unavailable during startup. Reconnect it and retry discovery.", { cause: error });
  if (operation === "playback") return new MediaLifecycleError("playback_failure", "The camera stream opened but its local preview could not start. Retry after releasing the camera.", { cause: error });
  return new MediaLifecycleError("unknown", "Camera discovery failed. Release other camera sessions and retry.", { cause: error });
}

function withTimeout<T>(task: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = globalThis.setTimeout(() => reject(new MediaLifecycleError("acquisition_timeout", `Camera acquisition did not complete within ${Math.round(timeoutMs / 1000)} seconds.`)), timeoutMs);
    task.then((value) => { globalThis.clearTimeout(timer); resolve(value); }, (error) => { globalThis.clearTimeout(timer); reject(error); });
  });
}

export async function discoverVideoDevices(timeoutMs = 10000): Promise<{ devices: MediaDeviceInfo[]; allDevices: MediaDeviceInfo[] }> {
  if (!navigator.mediaDevices?.getUserMedia || !navigator.mediaDevices.enumerateDevices) throw new MediaLifecycleError("unsupported", "This browser does not expose the required media-device APIs.");
  let permissionStream: MediaStream | null = null;
  try {
    permissionStream = await withTimeout(navigator.mediaDevices.getUserMedia({ video: true, audio: false }), timeoutMs);
    const allDevices = await navigator.mediaDevices.enumerateDevices();
    const devices = allDevices.filter((device) => device.kind === "videoinput");
    if (!devices.length) throw new MediaLifecycleError("no_device", "Camera permission was granted, but no video-input device was returned. Reconnect the camera and retry discovery.");
    return { devices, allDevices };
  } catch (error) {
    throw classifyMediaError(error);
  } finally {
    stopMediaStream(permissionStream);
  }
}
