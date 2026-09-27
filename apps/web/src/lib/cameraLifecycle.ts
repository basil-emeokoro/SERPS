/** One owner per assigned camera; temporary mute never discards a live track. */
export class AssignedCamera {
  stream: MediaStream | null = null;
  private disposed = false;
  private pending: Promise<void> | null = null;
  private detach: (() => void) | null = null;
  private state = "connecting";
  private everConnected = false;
  constructor(private deviceId: string, private video: () => HTMLVideoElement | null,
    private changed: (state: string, reason: string, recovered: boolean) => void) {}

  private publish(state: string, reason: string) {
    if (this.disposed || state === this.state) return;
    const recovered = state === "connected" && this.everConnected;
    this.state = state;
    if (state === "connected") this.everConnected = true;
    this.changed(state, reason, recovered);
  }
  private inspect = () => {
    if (!this.stream || this.disposed) return;
    const tracks = this.stream.getVideoTracks();
    const ended = tracks.length === 0 || tracks.every(t => t.readyState === "ended");
    const muted = tracks.some(t => t.muted);
    this.publish(ended ? "ended" : muted ? "muted" : this.stream.active ? "connected" : "unavailable",
      ended ? "track ended" : muted ? "track temporarily muted" : this.stream.active ? "live track available" : "stream inactive");
  };
  connect(): Promise<void> {
    if (this.disposed) return Promise.resolve();
    if (this.pending) return this.pending;
    // A live muted track remains owned; unmute recovers without competing acquisition.
    if (this.stream?.getVideoTracks().some(t => t.readyState === "live")) {
      this.inspect();
      return this.video()?.play().catch(() => undefined) ?? Promise.resolve();
    }
    this.pending = this.acquire().finally(() => { this.pending = null; });
    return this.pending;
  }
  private async acquire() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: this.deviceId } }, audio: false });
      if (this.disposed) { stream.getTracks().forEach(t => t.stop()); return; }
      this.release();
      this.stream = stream;
      const video = this.video();
      if (video) { video.srcObject = stream; await video.play().catch(() => undefined); }
      if (this.disposed) return;
      const tracks = stream.getVideoTracks();
      for (const track of tracks) for (const event of ["ended", "mute", "unmute"]) track.addEventListener(event, this.inspect);
      stream.addEventListener("inactive", this.inspect);
      this.detach = () => {
        for (const track of tracks) for (const event of ["ended", "mute", "unmute"]) track.removeEventListener(event, this.inspect);
        stream.removeEventListener("inactive", this.inspect);
      };
      this.inspect();
    } catch (error) {
      this.publish("unavailable", error instanceof Error ? error.name + ": " + error.message : "camera acquisition failed");
    }
  }
  private release() {
    this.detach?.(); this.detach = null;
    const stream = this.stream;
    this.stream = null;
    if (this.video()?.srcObject === stream) this.video()!.srcObject = null;
    stream?.getTracks().forEach(t => t.stop());
  }
  close() { this.disposed = true; this.release(); }
}

/** Reject repeat/frozen frames; unavailable is never a zero-person observation. */
export class FreshCameraFrame {
  private source: MediaStream | null = null;
  private time = -1;
  available(stream: MediaStream | null | undefined, video: HTMLVideoElement | null): boolean {
    if (!stream?.active || !stream.getVideoTracks().some(t => t.readyState === "live" && !t.muted)
      || !video || video.srcObject !== stream || video.readyState < 2 || video.paused
      || video.videoWidth === 0 || video.videoHeight === 0) return false;
    const quality = video.getVideoPlaybackQuality?.();
    const frame = quality ? quality.totalVideoFrames : video.currentTime;
    if (quality && frame === 0) return false;
    if (this.source === stream && frame <= this.time) return false;
    this.source = stream; this.time = frame;
    return true;
  }
}


// Track snapshots are independent of preview painting (which browsers throttle off-screen).
type TrackCapture = { grabFrame(): Promise<ImageBitmap> };
type CaptureConstructor = new (track: MediaStreamTrack) => TrackCapture;
export class CameraFrameSampler {
  private fallback = new FreshCameraFrame();
  private track: MediaStreamTrack | null = null;
  private capture: TrackCapture | null = null;
  private busy = false;
  private disposed = false;

  close() { this.disposed = true; this.capture = null; this.track = null; }

  async sample(stream: MediaStream | null | undefined, video: HTMLVideoElement | null,
    consume: (frame: HTMLVideoElement | ImageBitmap) => void): Promise<boolean> {
    const track = stream?.getVideoTracks()[0];
    const healthy = () => !this.disposed && !!stream?.active && track?.readyState === "live" && !track.muted && stream.getVideoTracks()[0] === track;
    if (!healthy() || this.busy) return false;
    const Capture = (globalThis as typeof globalThis & { ImageCapture?: CaptureConstructor }).ImageCapture;
    if (!Capture) {
      if (!this.fallback.available(stream, video)) return false;
      consume(video!); return true;
    }
    if (this.track !== track) { this.capture = new Capture(track!); this.track = track!; }
    const capture = this.capture!;
    this.busy = true;
    const started = performance.now();
    let expired = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const pending = Promise.resolve().then(() => capture.grabFrame()).then(frame => {
      try {
        if (expired || !healthy() || performance.now() - started > 1500 || !frame.width || !frame.height) return false;
        consume(frame); return true;
      } finally { frame.close(); }
    }).finally(() => { this.busy = false; });
    try {
      return await Promise.race([pending, new Promise<boolean>(resolve => {
        timer = setTimeout(() => { expired = true; resolve(false); }, 1500);
      })]);
    } finally { clearTimeout(timer); }
  }
}
