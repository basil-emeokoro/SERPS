export const AUDIO_MONITOR_NAME = "Web Audio RMS Activity Monitor";
export const AUDIO_MONITOR_VERSION = "SERPS-AUDIO-1.0";
export const DEFAULT_AUDIO_THRESHOLD = 0.08;
export const AUDIO_SAMPLE_INTERVAL_MS = 200;
export const AUDIO_ACTIVITY_MIN_MS = 600;
export const AUDIO_SUSTAINED_MIN_MS = 2500;
export const AUDIO_EVENT_COOLDOWN_MS = 10000;

export type AudioActivityKind = "audio_activity_detected" | "sustained_audio_activity";

export type AudioActivitySignal = {
  kind: AudioActivityKind;
  normalizedLevel: number;
  threshold: number;
  durationMs: number;
  recurrenceCount: number;
};

function configuredThreshold(): number {
  const candidate = Number(process.env.NEXT_PUBLIC_AUDIO_ACTIVITY_THRESHOLD ?? DEFAULT_AUDIO_THRESHOLD);
  return Number.isFinite(candidate) && candidate >= 0.01 && candidate <= 0.8
    ? candidate
    : DEFAULT_AUDIO_THRESHOLD;
}

export class AudioActivityTracker {
  private activityStartedAt: number | null = null;
  private activityEmitted = false;
  private sustainedEmitted = false;
  private recurrenceCount = 0;
  private lastEmittedAt: Record<AudioActivityKind, number> = {
    audio_activity_detected: Number.NEGATIVE_INFINITY,
    sustained_audio_activity: Number.NEGATIVE_INFINITY,
  };

  constructor(
    readonly threshold = configuredThreshold(),
    private readonly activityMinMs = AUDIO_ACTIVITY_MIN_MS,
    private readonly sustainedMinMs = AUDIO_SUSTAINED_MIN_MS,
    private readonly cooldownMs = AUDIO_EVENT_COOLDOWN_MS,
  ) {}

  update(level: number, nowMs: number): AudioActivitySignal[] {
    const normalizedLevel = Math.max(0, Math.min(level, 1));
    if (normalizedLevel < this.threshold) {
      this.activityStartedAt = null;
      this.activityEmitted = false;
      this.sustainedEmitted = false;
      return [];
    }
    if (this.activityStartedAt == null) this.activityStartedAt = nowMs;
    const durationMs = Math.max(0, nowMs - this.activityStartedAt);
    const signals: AudioActivitySignal[] = [];
    if (!this.activityEmitted && durationMs >= this.activityMinMs && nowMs - this.lastEmittedAt.audio_activity_detected >= this.cooldownMs) {
      this.activityEmitted = true;
      this.recurrenceCount += 1;
      this.lastEmittedAt.audio_activity_detected = nowMs;
      signals.push({ kind: "audio_activity_detected", normalizedLevel, threshold: this.threshold, durationMs, recurrenceCount: this.recurrenceCount });
    }
    if (!this.sustainedEmitted && durationMs >= this.sustainedMinMs && nowMs - this.lastEmittedAt.sustained_audio_activity >= this.cooldownMs) {
      this.sustainedEmitted = true;
      this.lastEmittedAt.sustained_audio_activity = nowMs;
      signals.push({ kind: "sustained_audio_activity", normalizedLevel, threshold: this.threshold, durationMs, recurrenceCount: this.recurrenceCount });
    }
    return signals;
  }
}

export class LocalAudioMonitor {
  private context: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private samples = new Float32Array(2048);
  private stream: MediaStream | null = null;

  async start(): Promise<MediaStream> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
      video: false,
    });
    this.context = new AudioContext();
    if (this.context.state === "suspended") await this.context.resume();
    this.analyser = this.context.createAnalyser();
    this.analyser.fftSize = 2048;
    this.analyser.smoothingTimeConstant = 0.2;
    this.source = this.context.createMediaStreamSource(this.stream);
    this.source.connect(this.analyser);
    return this.stream;
  }

  sampleLevel(): number {
    if (!this.analyser) throw new Error("The audio monitor has not started.");
    this.analyser.getFloatTimeDomainData(this.samples);
    let sumSquares = 0;
    for (const sample of this.samples) sumSquares += sample * sample;
    return Math.max(0, Math.min(Math.sqrt(sumSquares / this.samples.length), 1));
  }

  async close(): Promise<void> {
    this.source?.disconnect();
    this.analyser?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    if (this.context && this.context.state !== "closed") await this.context.close();
    this.context = null;
    this.analyser = null;
    this.source = null;
    this.stream = null;
  }
}
