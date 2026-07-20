"use client";

import type { CameraStatus } from "../lib/contracts";
import { cameraStatusText, riskClass } from "../lib/operational";

export function LoadingState({ label = "Loading operational data..." }: { label?: string }) {
  return <section className="state-card" role="status" aria-live="polite"><span className="spinner" aria-hidden="true" /><p>{label}</p></section>;
}
export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <section className="state-card"><span className="status-badge neutral">No results</span><h2>{title}</h2><p>{detail}</p></section>;
}
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <section className="state-card error-state" role="alert"><span className="status-badge danger">API failure</span><h2>Unable to load this view</h2><p>{message}</p>{onRetry && <button onClick={onRetry}>Retry</button>}</section>;
}
export function StatusBadge({ label, tone = "neutral" }: { label: string; tone?: "neutral" | "success" | "warning" | "danger" }) {
  return <span className={`status-badge ${tone}`}>{label}</span>;
}
export function RiskIndicator({ level, score }: { level: string | null; score?: number | null }) {
  return <div className={`risk-indicator ${riskClass(level)}`} aria-label={`Risk level ${level ?? "unavailable"}${score == null ? "" : `, score ${score.toFixed(2)}`}`}><strong>{level ?? "Unavailable"}</strong>{score != null && <span>{score.toFixed(2)}</span>}</div>;
}
export function ReadinessSummary({ readiness }: { readiness: Record<string, boolean> }) {
  return <div className="state-list" aria-label="Candidate session readiness">{Object.entries(readiness).map(([name, passed]) => <span className={passed ? "state-pass" : "state-fail"} key={name}>{name.replaceAll("_", " ")}: {passed ? "pass" : "fail"}</span>)}</div>;
}
export function FeatureCapability({ label, supported, fallback }: { label: string; supported: boolean; fallback: string }) {
  return <div className={supported ? "capability-disclosure supported" : "capability-disclosure"} role="status"><strong>{label}:</strong> {supported ? "Supported" : `Unavailable — ${fallback}`}</div>;
}
export function MetricCards({ metrics }: { metrics: { label: string; value: number }[] }) {
  return <section className="metric-grid" aria-label="Institution operational metrics">{metrics.map((metric) => <article className="metric-card" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong></article>)}</section>;
}
export function CameraPanel({ camera, title }: { camera: CameraStatus; title: string }) {
  const tone = camera.connection_status === "connected" ? "success" : camera.connection_status === "disconnected" ? "danger" : "warning";
  return <article className="camera-panel" aria-label={`${title} status`}>
    <div className="camera-placeholder" role="img" aria-label={`${title}: remote video streaming unavailable in this prototype`}><span>{title}</span><small>Metadata-only reviewer view — no fabricated video</small></div>
    <div className="camera-meta"><StatusBadge label={camera.connection_status.replaceAll("_", " ")} tone={tone} /><strong>{camera.label ?? "No privacy-safe label available"}</strong><span>{cameraStatusText(camera)}</span><span>Last seen: {camera.last_seen_at ? new Date(camera.last_seen_at).toLocaleString() : "No event observed"}</span>{camera.failure_reason && <span className="danger-text">{camera.failure_reason}</span>}</div>
  </article>;
}

export function ConfirmationDialog({ open, title, detail, confirmLabel, onConfirm, onCancel }: { open: boolean; title: string; detail: string; confirmLabel: string; onConfirm: () => void; onCancel: () => void }) {
  if (!open) return null;
  return <div className="dialog-backdrop" role="presentation"><section className="confirmation-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirmation-title" aria-describedby="confirmation-detail"><h2 id="confirmation-title">{title}</h2><p id="confirmation-detail">{detail}</p><div className="dialog-actions"><button onClick={onCancel}>Cancel</button><button className="primary-action" onClick={onConfirm}>{confirmLabel}</button></div></section></div>;
}
