import { afterEach, expect, it, vi } from "vitest";
import { EvidenceOutbox } from "./evidenceDelivery";
import { ApiError, NetworkError } from "./api";
const payload = { session_id: "S", candidate_id: "C", event_type: "face_detected", description: "Synthetic event" };
function storage() { const values = new Map<string, string>(); return { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => { values.set(k, v); } }; }
afterEach(() => vi.useRealTimers());
it("retains identity/order through lost acknowledgements and bounded retries", async () => {
  vi.useFakeTimers(); const store = storage();
  const send = vi.fn().mockRejectedValue(new NetworkError("offline"));
  const queue = new EvidenceOutbox("key", store, send);
  queue.enqueue(payload); queue.enqueue({ ...payload, event_type: "face_not_detected" });
  await queue.flush(); await vi.advanceTimersByTimeAsync(4000);
  expect(send).toHaveBeenCalledTimes(3); expect(queue.snapshot().pending).toBe(2);
  const first = send.mock.calls[0][0]; expect(send.mock.calls.every(([p]) => p === first)).toBe(true);
  expect(queue.snapshot().failure).toContain("unresolved");
  send.mockResolvedValue({}); queue.retry(); await queue.flush();
  expect(send.mock.calls[3][0]).toBe(first);
  expect(send.mock.calls[4][0].event_type).toBe("face_not_detected");
  expect(queue.snapshot().pending).toBe(0);
});
it("restores unsent metadata on remount and does not retry authorization errors automatically", async () => {
  const store = storage(); const send = vi.fn().mockRejectedValue(new ApiError("Forbidden", 403));
  const first = new EvidenceOutbox("key", store, send); first.enqueue(payload); await first.flush(); first.pause();
  const second = new EvidenceOutbox("key", store, send); await second.flush();
  expect(second.snapshot().pending).toBe(1); expect(send).toHaveBeenCalledTimes(1);
  send.mockResolvedValue({}); second.retry(); await second.flush();
  expect(send.mock.calls[1][0]).toEqual(send.mock.calls[0][0]);
});
it("retains memory and reports storage failure rather than discarding events", async () => {
  const store = { getItem: () => null, setItem: () => { throw new Error("Quota"); } };
  const queue = new EvidenceOutbox("key", store, vi.fn().mockRejectedValue(new ApiError("Forbidden", 403)));
  queue.enqueue(payload); await queue.flush();
  expect(queue.snapshot()).toMatchObject({ pending: 1, durable: false });
  expect(queue.snapshot().failure).toContain("memory");
});
it.each(["corrupt", JSON.stringify({ sequence: 1, entries: [null] })])("preserves corrupt persisted evidence without overwriting it: %s", async saved => {
  const setItem = vi.fn(); const queue = new EvidenceOutbox("key", { getItem: () => saved, setItem });
  queue.enqueue(payload); await queue.flush();
  expect(setItem).not.toHaveBeenCalled(); expect(queue.snapshot().failure).toContain("not been overwritten");
});

it("cannot clear a corrupt-queue barrier by retrying before any new event arrives", async () => {
  const store = storage(); store.setItem("key", "unreadable retained evidence");
  const send = vi.fn(); const queue = new EvidenceOutbox("key", store, send);
  queue.retry(); await queue.flush();
  expect(queue.snapshot().failure).toContain("not been overwritten");
  expect(queue.snapshot().durable).toBe(false);
  expect(store.getItem("key")).toBe("unreadable retained evidence");
  expect(send).not.toHaveBeenCalled();
});
