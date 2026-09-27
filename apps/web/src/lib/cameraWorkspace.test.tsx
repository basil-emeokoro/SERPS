// @vitest-environment jsdom
import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Workspace from "../app/candidate/examinations/[sessionId]/page";
import { completeCandidateSession, fetchCandidateWorkspace, fetchCandidateProtection, submitEvidenceEvent } from "./api";
vi.mock("next/navigation", () => ({ useParams: () => ({ sessionId: "S" }) }));
vi.mock("../components/PortalShell", () => ({ PortalShell: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }));
vi.mock("../components/FacialVerification", () => ({ default: () => <div>Identity check</div> }));
vi.mock("./api", () => ({ completeCandidateSession: vi.fn(), fetchCandidateWorkspace: vi.fn(), fetchCandidateProtection: vi.fn(), submitEvidenceEvent: vi.fn(), updateDemoPhonePolicy: vi.fn() }));
vi.mock("./reauthentication", () => ({ fetchReauthentication: vi.fn().mockResolvedValue({ required: false }), reauthenticationMessage: () => "" }));
vi.mock("./objectDetection", () => ({ OBJECT_MODEL_NAME: "Test detector", OBJECT_MODEL_VERSION: "test", OBJECT_SAMPLE_INTERVAL_MS: 1500,
  LocalObjectDetector: class { async initialise() {} close() {} detect() { if (inferenceFails) throw new Error("Synthetic inference failure"); return { personCount: 1, mobilePhoneCount: 0, processingTime: 1, modelName: "test", modelVersion: "test", threshold: .55, detections: [{ detectedClass: "person", confidence: .9 }] }; } } }));
vi.mock("./faceDetection", async importOriginal => ({ ...await importOriginal<typeof import("./faceDetection")>(), LocalFacePerceptionService: class { async initialise() {} close() {} detect() { return { faceCount: faceAbsent ? 0 : 1, faces: [], processingTime: 1, confidence: null }; } } }));
vi.mock("./audioMonitoring", () => ({ AUDIO_MONITOR_NAME: "test", AUDIO_MONITOR_VERSION: "test", AUDIO_SAMPLE_INTERVAL_MS: 500,
  AudioActivityTracker: class { update() { return []; } }, LocalAudioMonitor: class { async start() { return { getAudioTracks: () => [] }; } sampleLevel() { return 0; } async close() {} } }));
let tracks: Array<EventTarget & { readyState: string; muted: boolean; stop: ReturnType<typeof vi.fn> }>;
let getUserMedia: ReturnType<typeof vi.fn>;
let frozen = false;
let faceAbsent = false;
let inferenceFails = false;
beforeEach(() => {
  vi.useFakeTimers(); vi.clearAllMocks(); tracks = []; frozen = false; faceAbsent = false; inferenceFails = false;
  vi.mocked(fetchCandidateProtection).mockResolvedValue({ state: "NORMAL", demo_controls_enabled: false, demo_phone_policy_armed: false } as never);
  vi.mocked(submitEvidenceEvent).mockResolvedValue({} as never); vi.mocked(completeCandidateSession).mockResolvedValue({} as never);
  getUserMedia = vi.fn(async () => {
    const t = Object.assign(new EventTarget(), { readyState: "live", muted: false, stop: vi.fn(() => { t.readyState = "ended"; }) }); tracks.push(t);
    return Object.assign(new EventTarget(), { get active() { return t.readyState === "live"; }, getVideoTracks: () => [t], getTracks: () => [t] });
  });
  Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: Object.assign(new EventTarget(), { getUserMedia }) });
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  for (const [k, value] of Object.entries({ readyState: 4, paused: false, videoWidth: 640, videoHeight: 480 })) Object.defineProperty(HTMLVideoElement.prototype, k, { configurable: true, get: () => value });
  Object.defineProperty(HTMLVideoElement.prototype, "currentTime", { configurable: true, get: () => frozen ? 0 : Date.now() / 1000 });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });
async function open(mode = "B", enrolled = false) {
  vi.mocked(fetchCandidateWorkspace).mockResolvedValue({ session: { session_id: "S", status: "active", deployment_mode: mode, started_at: new Date().toISOString() }, candidate: { candidate_id: "C", full_name: enrolled ? "Enrolled candidate" : "Demo candidate" }, institution: { name: "Test institution" }, examination: { title: "Test examination" }, primary_camera: { device_id: "C1" }, secondary_camera: mode === "B" ? { device_id: "C2" } : null } as never);
  const view = render(<Workspace />); await act(async () => { await vi.advanceTimersByTimeAsync(0); }); return view;
}
it.each(["A", "B", "C"].flatMap(mode => [false, true].map(enrolled => ({ mode, enrolled }))))("keeps required cameras alive through state/polling cycles: $mode enrolled=$enrolled", async ({ mode, enrolled }) => {
  const view = await open(mode, enrolled);
  await act(async () => { await vi.advanceTimersByTimeAsync(31000); });
  fireEvent.click(screen.getByText("Next")); view.rerender(<Workspace />);
  expect(getUserMedia).toHaveBeenCalledTimes(mode === "B" ? 2 : 1);
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled());
  view.unmount(); tracks.forEach(t => expect(t.stop).toHaveBeenCalledTimes(1));
});
it("invalidates counts immediately on mute, records loss, and recovers original stream on unmute", async () => {
  await open(); await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.getAllByText(/1 person\(s\)/)).toHaveLength(2);
  await act(async () => { tracks[1].muted = true; tracks[1].dispatchEvent(new Event("mute")); await vi.advanceTimersByTimeAsync(5000); });
  expect(screen.getAllByText(/1 person\(s\)/)).toHaveLength(1);
  expect(screen.getByText(/No current observation/)).toBeTruthy();
  expect(screen.queryByText(/0 person\(s\)/)).toBeNull();
  expect(vi.mocked(submitEvidenceEvent).mock.calls.some(([e]) => e.event_type === "camera_disconnected" && e.camera_id === "secondary")).toBe(true);
  await act(async () => { tracks[1].muted = false; tracks[1].dispatchEvent(new Event("unmute")); await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.getAllByText(/1 person\(s\)/)).toHaveLength(2); expect(getUserMedia).toHaveBeenCalledTimes(2);
  expect(vi.mocked(submitEvidenceEvent).mock.calls.some(([e]) => e.event_type === "camera_reconnected")).toBe(true);
});
it("invalidates frozen frames and emits no new positive detection from them", async () => {
  await open(); frozen = true; await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  const positives = () => vi.mocked(submitEvidenceEvent).mock.calls.filter(([e]) => e.event_type === "person_detected").length;
  const before = positives(); await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
  expect(positives()).toBe(before); expect(screen.getAllByText(/No current observation/)).toHaveLength(2);
});
it("keeps cameras alive when completion fails and releases after successful completion", async () => {
  await open(); vi.mocked(completeCandidateSession).mockRejectedValueOnce(new Error("Completion unavailable"));
  fireEvent.click(screen.getByText("Finish demonstration")); fireEvent.click(screen.getAllByText("Finish demonstration").at(-1)!);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); }); tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled());
  fireEvent.click(screen.getByText("Finish demonstration")); fireEvent.click(screen.getAllByText("Finish demonstration").at(-1)!);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); }); tracks.forEach(t => expect(t.stop).toHaveBeenCalledTimes(1));
});

it("preserves camera ownership on resize, blur, background and foreground; clears stale readings", async () => {
  await open(); await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  act(() => { window.dispatchEvent(new Event("resize")); window.dispatchEvent(new Event("blur")); });
  Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
  act(() => { document.dispatchEvent(new Event("visibilitychange")); });
  expect(screen.queryByText(/1 person\(s\)/)).toBeNull();
  await act(async () => { await vi.advanceTimersByTimeAsync(20000); });
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled()); expect(getUserMedia).toHaveBeenCalledTimes(2);
  Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
  await act(async () => { document.dispatchEvent(new Event("visibilitychange")); window.dispatchEvent(new Event("focus")); await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.getAllByText(/1 person\(s\)/)).toHaveLength(2); expect(getUserMedia).toHaveBeenCalledTimes(2);
});
it("reconnects an ended secondary without stopping the primary, preserving loss and recovery evidence", async () => {
  await open();
  await act(async () => { tracks[1].readyState = "ended"; tracks[1].dispatchEvent(new Event("ended")); await vi.advanceTimersByTimeAsync(5000); });
  await act(async () => { navigator.mediaDevices.dispatchEvent(new Event("devicechange")); await vi.advanceTimersByTimeAsync(1500); });
  expect(getUserMedia).toHaveBeenCalledTimes(3); expect(tracks[0].stop).not.toHaveBeenCalled();
  const events = vi.mocked(submitEvidenceEvent).mock.calls.map(([e]) => e.event_type);
  expect(events).toContain("camera_disconnected"); expect(events).toContain("camera_reconnected");
});

it("sustained face absence remains evidence and does not tear down either camera", async () => {
  await open(); faceAbsent = true;
  await act(async () => { await vi.advanceTimersByTimeAsync(12000); });
  expect(vi.mocked(submitEvidenceEvent).mock.calls.some(([e]) => e.event_type === "sustained_face_absence")).toBe(true);
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled()); expect(getUserMedia).toHaveBeenCalledTimes(2);
});

it("temporary mute recovers without a permanent-disconnection event or stream replacement", async () => {
  await open();
  await act(async () => { tracks[0].muted = true; tracks[0].dispatchEvent(new Event("mute")); await vi.advanceTimersByTimeAsync(1000); tracks[0].muted = false; tracks[0].dispatchEvent(new Event("unmute")); await vi.advanceTimersByTimeAsync(5000); });
  expect(vi.mocked(submitEvidenceEvent).mock.calls.some(([e]) => e.event_type === "camera_disconnected")).toBe(false);
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled()); expect(getUserMedia).toHaveBeenCalledTimes(2);
});
it("inference failure clears previous counts and a successful new inference restores readiness", async () => {
  await open(); await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  inferenceFails = true; await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.queryByText(/1 person\(s\)/)).toBeNull(); expect(screen.queryByText(/0 person\(s\)/)).toBeNull();
  expect(screen.getAllByText(/No current observation/)).toHaveLength(2);
  inferenceFails = false; await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.getAllByText(/1 person\(s\)/)).toHaveLength(2);
});

async function connectivityLoss() {
  vi.mocked(fetchCandidateProtection).mockRejectedValue(new Error("Synthetic offline"));
  await act(async () => { await vi.advanceTimersByTimeAsync(21000); });
  expect(screen.getByRole("alertdialog")).toBeTruthy();
}
function onlinePolicy(protectedBy?: string) {
  vi.mocked(fetchCandidateProtection).mockResolvedValue({ state: protectedBy ? "PROTECTED" : "NORMAL", policy_action: protectedBy ? "PROTECT_AND_PAUSE" : null, reason_category: protectedBy, requires_reviewer: !!protectedBy, demo_controls_enabled: false, demo_phone_policy_armed: false } as never);
}
it("connectivity recovery with ready monitoring resumes without restarting cameras", async () => {
  await open(); await connectivityLoss(); onlinePolicy();
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(screen.queryByRole("alertdialog")).toBeNull();
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled()); expect(getUserMedia).toHaveBeenCalledTimes(2);
});
it("holds after network recovery until subsequent monitoring readiness recovery, then resumes", async () => {
  await open(); await connectivityLoss();
  await act(async () => { tracks[1].muted = true; tracks[1].dispatchEvent(new Event("mute")); });
  onlinePolicy(); await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(screen.getByRole("alertdialog")).toBeTruthy();
  await act(async () => { tracks[1].muted = false; tracks[1].dispatchEvent(new Event("unmute")); await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.queryByRole("alertdialog")).toBeNull();
  const clear = vi.mocked(submitEvidenceEvent).mock.calls.filter(([e]) => e.event_type === "protection_cleared" && e.metadata_json?.trigger_category === "connectivity_interrupted");
  expect(clear).toHaveLength(1); expect(clear[0][0].metadata_json?.misconduct_determination).toBe(false);
  tracks.forEach(t => expect(t.stop).not.toHaveBeenCalled());
});
it.each(["phone_policy", "required_camera_unavailable"])("connectivity/readiness recovery preserves independent %s protection", async cause => {
  await open(); await connectivityLoss();
  await act(async () => { tracks[1].muted = true; tracks[1].dispatchEvent(new Event("mute")); });
  onlinePolicy(cause); await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  await act(async () => { tracks[1].muted = false; tracks[1].dispatchEvent(new Event("unmute")); await vi.advanceTimersByTimeAsync(1500); });
  expect(screen.getByRole("alertdialog").textContent).toContain("Policy review required");
  const clear = vi.mocked(submitEvidenceEvent).mock.calls.filter(([e]) => e.event_type === "protection_cleared" && e.metadata_json?.trigger_category === "connectivity_interrupted");
  expect(clear).toHaveLength(1); expect(clear[0][0].metadata_json?.protection_state).toBe("PROTECTED");
});
it("repeated outages recover once each and unmount stops polling and media", async () => {
  const view = await open();
  for (let i = 0; i < 2; i++) { await connectivityLoss(); onlinePolicy(); await act(async () => { await vi.advanceTimersByTimeAsync(10000); }); expect(screen.queryByRole("alertdialog")).toBeNull(); }
  const clear = vi.mocked(submitEvidenceEvent).mock.calls.filter(([e]) => e.event_type === "protection_cleared" && e.metadata_json?.trigger_category === "connectivity_interrupted");
  expect(clear).toHaveLength(2);
  view.unmount(); const calls = vi.mocked(fetchCandidateProtection).mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
  expect(fetchCandidateProtection).toHaveBeenCalledTimes(calls); tracks.forEach(t => expect(t.stop).toHaveBeenCalledTimes(1));
});
