import { ApiError, NetworkError, submitEvidenceEvent } from "./api";

type Payload = Parameters<typeof submitEvidenceEvent>[0];
type Entry = { payload: Payload; attempts: number };
function validEntry(value: unknown): value is Entry {
  if (!value || typeof value !== "object") return false;
  const entry = value as Record<string, unknown>;
  if (!Number.isInteger(entry.attempts) || Number(entry.attempts) < 0 || Number(entry.attempts) > 3 || !entry.payload || typeof entry.payload !== "object") return false;
  const payload = entry.payload as Record<string, unknown>;
  return ["session_id", "candidate_id", "event_type", "description", "timestamp"].every(key => typeof payload[key] === "string")
    && !!payload.metadata_json && typeof payload.metadata_json === "object"
    && typeof (payload.metadata_json as Record<string, unknown>).delivery_id === "string";
}
export type DeliveryState = { pending: number; failure: string; durable: boolean };
/** One ordered outbox per candidate/session in this tab. Raw media is never added. */
export class EvidenceOutbox {
  private entries: Entry[] = [];
  private running: Promise<void> | null = null;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private listeners = new Set<(state: DeliveryState) => void>();
  private failure = "";
  private durable = true;
  private paused = false;
  private sequence = 0;
  private corrupt = false;
  constructor(private key: string, private storage: Pick<Storage, "getItem" | "setItem">, private send = submitEvidenceEvent) {
    try {
      const saved = storage.getItem(key);
      if (saved) {
        const data = JSON.parse(saved);
        if (!data || !Array.isArray(data.entries) || !data.entries.every(validEntry) || !Number.isSafeInteger(data.sequence)) throw new Error();
        this.entries = data.entries; this.sequence = data.sequence;
      }
    } catch { this.corrupt = true; this.durable = false; this.failure = "Saved evidence queue could not be read. It has not been overwritten; delivery requires investigation."; }
  }
  snapshot(): DeliveryState { return { pending: this.entries.length, failure: this.failure, durable: this.durable }; }
  subscribe(listener: (state: DeliveryState) => void) {
    this.listeners.add(listener); listener(this.snapshot());
    return () => { this.listeners.delete(listener); };
  }
  private publish() { for (const listener of this.listeners) listener(this.snapshot()); }
  private persist() {
    if (this.corrupt) return;
    try { this.storage.setItem(this.key, JSON.stringify({ sequence: this.sequence, entries: this.entries })); this.durable = true; }
    catch { this.durable = false; this.failure = "Evidence is retained in memory only: browser storage failed. Keep this tab open and restore delivery."; }
  }
  enqueue(payload: Payload) {
    const timestamp = new Date().toISOString();
    this.entries.push({ payload: { ...payload, timestamp, metadata_json: { ...payload.metadata_json,
      delivery_id: crypto.randomUUID(), delivery_sequence: ++this.sequence, observed_at: timestamp } }, attempts: 0 });
    this.persist(); this.publish(); this.resume();
  }
  pause() { this.paused = true; clearTimeout(this.timer); this.timer = undefined; }
  resume() { this.paused = false; void this.flush(); }
  retry() {
    clearTimeout(this.timer); this.timer = undefined;
    for (const entry of this.entries) entry.attempts = 0;
    this.failure = ""; this.persist(); this.resume();
  }
  flush(): Promise<void> {
    if (this.running) return this.running;
    if (this.paused || this.corrupt || this.timer || !this.entries.length || this.entries[0].attempts >= 3) return Promise.resolve();
    this.running = this.drain().finally(() => {
      this.running = null; this.publish();
      if (!this.paused && !this.corrupt && !this.timer && this.entries.length && this.entries[0].attempts < 3) void this.flush();
    });
    return this.running;
  }
  private async drain() {
    while (!this.paused && this.entries.length) {
      const entry = this.entries[0];
      if (entry.attempts >= 3) return;
      entry.attempts++; this.persist();
      try {
        await this.send(entry.payload);
        this.entries.shift(); this.failure = ""; this.persist(); this.publish();
      } catch (error) {
        this.failure = `Evidence delivery unresolved (${this.entries.length} pending). ${error instanceof Error ? error.message : "Request failed."}`;
        const transient = error instanceof NetworkError || (error instanceof ApiError && (error.status >= 500 || error.status === 408 || error.status === 429));
        if (!transient) entry.attempts = 3;
        this.persist(); this.publish();
        if (!this.paused && transient && entry.attempts < 3) this.timer = setTimeout(() => {
          this.timer = undefined; void this.flush();
        }, 1000 * 2 ** (entry.attempts - 1));
        return;
      }
    }
  }
}
const outboxes = new Map<string, EvidenceOutbox>();
export function evidenceOutbox(candidate: string, session: string): EvidenceOutbox {
  const key = `serps_evidence_outbox:${candidate}:${session}`;
  let box = outboxes.get(key);
  if (!box) { box = new EvidenceOutbox(key, { getItem: k => sessionStorage.getItem(k), setItem: (k, v) => sessionStorage.setItem(k, v) }); outboxes.set(key, box); }
  return box;
}
