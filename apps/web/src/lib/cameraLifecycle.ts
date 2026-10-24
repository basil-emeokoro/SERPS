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


// Local diagnostics contain operational timings only; never frames or candidate identifiers.
export function recordFrameDiagnostic(detail: Record<string, unknown>) {
  const root = globalThis as typeof globalThis & { __serpsFrameDiagnostics?: Array<Record<string, unknown>> };
  const records = root.__serpsFrameDiagnostics ??= [];
  records.push({ at: Date.now(), pageTimeOrigin: performance.timeOrigin, ...detail });
  if (records.length > 200) records.splice(0, records.length - 200);
}

/** One fair queue for expensive detector work; repeated ticks never pile up. */
export class DetectorWorkQueue {
  private jobs = new Map<string, () => Promise<void>>();
  private active: string | null = null;
  private closed = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
  enqueue(key: string, work: () => Promise<void>) {
    if (this.closed || this.active === key || this.jobs.has(key)) return;
    this.jobs.set(key, work);
    recordFrameDiagnostic({ phase: "detector_queued", detector: key, activeDetector: this.active, detectorBusy: this.active !== null, queueDepth: this.jobs.size });
    this.schedule();
  }
  private schedule() {
    if (this.closed || this.active || this.timer != null || !this.jobs.size) return;
    this.timer = setTimeout(() => {
      this.timer = undefined;
      const [key, work] = this.jobs.entries().next().value!;
      this.jobs.delete(key); this.active = key;
      recordFrameDiagnostic({ phase: "detector_started", detector: key, detectorBusy: true, queueDepth: this.jobs.size });
      void work().catch(error => recordFrameDiagnostic({ phase: "queue_error", detector: key, error: String(error) }))
        .finally(() => { recordFrameDiagnostic({ phase: "detector_finished", detector: key, detectorBusy: false }); this.active = null; this.schedule(); });
    }, 0); // Yield for preview decoding, UI and media events between detectors.
  }
  close() { this.closed = true; clearTimeout(this.timer); this.jobs.clear(); }
}

const pendingTrackCaptures = new WeakSet<MediaStreamTrack>();

type TrackCapture = { grabFrame(): Promise<ImageBitmap> };
type CaptureConstructor = new (track: MediaStreamTrack) => TrackCapture;
export class CameraFrameSampler {
  private fallback = new FreshCameraFrame();
  private track: MediaStreamTrack | null = null;
  private capture: TrackCapture | null = null;
  private busy = false;
  private disposed = false;
  constructor(private diagnostic: (detail: Record<string, unknown>) => void = () => {}) {}
  close() { this.disposed = true; this.capture = null; this.track = null; }

  // true = sampled; null = pending/no new frame yet; false = actual source unavailable.
  async sample(stream: MediaStream | null | undefined, video: HTMLVideoElement | null,
    consume: (frame: HTMLVideoElement | ImageBitmap) => void): Promise<boolean | null> {
    const track = stream?.getVideoTracks()[0];
    const healthy = () => !this.disposed && !!stream?.active && track?.readyState === "live" && !track.muted && stream.getVideoTracks()[0] === track;
    const report = (detail: Record<string, unknown>) => this.diagnostic({
      trackState: track?.readyState ?? "missing", muted: track?.muted ?? null,
      streamActive: stream?.active ?? false, hidden: document.hidden, busy: this.busy,
      previewPaused: video?.paused ?? null, previewReadyState: video?.readyState ?? null,
      previewFrames: video?.getVideoPlaybackQuality?.().totalVideoFrames ?? null,
      previewTime: video?.currentTime ?? null, captureTimeout: false, lateFrameRejected: false, ...detail,
    });
    if (!healthy()) { report({ phase: "source_unavailable" }); return false; }
    // Foreground is the stable direct-video path, with no asynchronous capture deadline.
    const fresh = this.fallback.available(stream, video);
    if (fresh) {
      const start = performance.now();
      try { consume(video!); return true; }
      catch (error) { report({ phase: "inference_error", source: "preview", inferenceMs: performance.now() - start, error: String(error) }); throw error; }
      finally { report({ phase: "inference", source: "preview", previewFresh: true, acquisitionMs: 0, inferenceMs: performance.now() - start }); }
    }
    if (!document.hidden) { report({ phase: "waiting_frame", source: "preview", previewFresh: false }); return null; }
    if (this.busy || pendingTrackCaptures.has(track!)) { report({ phase: "capture_busy", source: "track", busy: true, previewFresh: false }); return null; }
    const Capture = (globalThis as typeof globalThis & { ImageCapture?: CaptureConstructor }).ImageCapture;
    if (!Capture) { report({ phase: "waiting_frame", source: "preview", previewFresh: false }); return null; }
    if (this.track !== track) { this.capture = new Capture(track!); this.track = track!; }
    const capture = this.capture!;
    this.busy = true;
    pendingTrackCaptures.add(track!);
    const started = performance.now();
    let expired = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const pending = Promise.resolve().then(() => capture.grabFrame()).catch(error => {
      report({ phase: "capture_error", source: "track", acquisitionMs: performance.now() - started, error: String(error) }); throw error;
    }).then(frame => {
      const acquisitionMs = performance.now() - started;
      try {
        if (expired || acquisitionMs > 1500 || this.disposed) { report({ phase: "late_frame_rejected", source: "track", acquisitionMs, lateFrameRejected: true }); return null; }
        if (!healthy()) { report({ phase: "source_unavailable", source: "track", acquisitionMs }); return false; }
        if (!frame.width || !frame.height) { report({ phase: "empty_frame", source: "track", acquisitionMs }); return null; }
        const inferenceStart = performance.now();
        try { consume(frame); return true; }
        catch (error) { report({ phase: "inference_error", source: "track", inferenceMs: performance.now() - inferenceStart, error: String(error) }); throw error; }
        finally { report({ phase: "inference", source: "track", acquisitionMs, inferenceMs: performance.now() - inferenceStart }); }
      } finally { frame.close(); }
    }).finally(() => { this.busy = false; pendingTrackCaptures.delete(track!); });
    try {
      return await Promise.race([pending, new Promise<null>(resolve => {
        timer = setTimeout(() => {
          expired = true;
          report({ phase: "capture_timeout", source: "track", acquisitionMs: performance.now() - started, captureTimeout: true });
          resolve(null);
        }, 1500);
      })]);
    } finally { clearTimeout(timer); }
  }
}
