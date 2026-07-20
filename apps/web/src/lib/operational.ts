import type { CameraStatus, Role } from "./contracts";

export function navigationForRoles(roles: Role[]): { href: string; label: string }[] {
  const links = [{ href: "/", label: "Home" }];
  if (roles.includes("Candidate")) links.push({ href: "/candidate", label: "Candidate" });
  if (roles.includes("Reviewer/Proctor")) links.push({ href: "/reviewer", label: "Reviewer" });
  if (roles.includes("Administrator")) links.push({ href: "/admin", label: "Administrator" });
  if (roles.includes("System Administrator")) links.push({ href: "/reviewer", label: "Reviewer" }, { href: "/admin", label: "Administrator" }, { href: "/system-admin", label: "System" });
  return links.filter((link, index, all) => all.findIndex((item) => item.href === link.href) === index);
}
export function riskClass(level: string | null | undefined): string { return `risk-${(level ?? "unknown").toLowerCase()}`; }
export function validateCameraPair(primaryId: string, secondaryId: string): string | null {
  if (!primaryId || !secondaryId) return "Two camera devices are required for dual-camera readiness.";
  if (primaryId === secondaryId) return "Primary and secondary cameras must be different physical devices.";
  return null;
}
export function validateReviewerDecision(decision: string, rationale: string): string | null {
  if (!decision) return "Select a reviewer decision.";
  if (!rationale.trim()) return "Reviewer rationale is required.";
  return null;
}
export function formatElapsed(startedAt: string, nowMs: number): string {
  const seconds = Math.max(0, Math.floor((nowMs - new Date(startedAt).getTime()) / 1000));
  return `${Math.floor(seconds / 3600).toString().padStart(2, "0")}:${Math.floor((seconds % 3600) / 60).toString().padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
}
export function cameraStatusText(camera: CameraStatus): string {
  if (!camera.configured) return `${camera.role} camera unavailable`;
  if (camera.connection_status === "connected") return `${camera.role} camera connected`;
  if (camera.connection_status === "disconnected") return `${camera.role} camera disconnected`;
  return `${camera.role} camera configured; no live remote stream`;
}
