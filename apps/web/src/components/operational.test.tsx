import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CameraPanel, ErrorState, FeatureCapability, LoadingState, MetricCards, ReadinessSummary, RiskIndicator } from "./OperationalStates";
import { RoleNavigation } from "./RoleNavigation";
import { formatElapsed, reviewerDetailPresentation, validateCameraPair, validateReviewerDecision } from "../lib/operational";

describe("operational portal components", () => {
  it("renders loading and API failure states accessibly", () => {
    expect(renderToStaticMarkup(<LoadingState />)).toContain('role="status"');
    expect(renderToStaticMarkup(<ErrorState message="Network unavailable" />)).toContain('role="alert"');
  });
  it("renders role-aware navigation without unauthorised links", () => {
    const markup = renderToStaticMarkup(<RoleNavigation user={{ user_id: "1", institution_id: "I", email: "c@example.test", full_name: "Candidate", roles: ["Candidate"] }} />);
    expect(markup).toContain("Candidate");
    expect(markup).not.toContain("Administrator");
  });
  it("renders candidate readiness with text in addition to colour", () => {
    const markup = renderToStaticMarkup(<ReadinessSummary readiness={{ primary_camera_selected: true, secondary_camera_selected: false }} />);
    expect(markup).toContain("primary camera selected: pass");
    expect(markup).toContain("secondary camera selected: fail");
  });
  it("renders dual-camera permission and unavailable states honestly", () => {
    const primary = renderToStaticMarkup(<CameraPanel title="Primary camera" camera={{ role: "primary", configured: true, connection_status: "connected", last_seen_at: null, label: "Primary", stream_mode: "metadata_only", failure_reason: null }} />);
    const secondary = renderToStaticMarkup(<CameraPanel title="Secondary camera" camera={{ role: "secondary", configured: false, connection_status: "not_seen", last_seen_at: null, label: null, stream_mode: "metadata_only", failure_reason: "Permission denied" }} />);
    expect(primary).toContain("no fabricated video");
    expect(secondary).toContain("secondary camera unavailable");
  });
  it("renders reviewer risk and administrator metrics", () => {
    expect(renderToStaticMarkup(<RiskIndicator level="Critical" score={0.91} />)).toContain("Critical");
    expect(renderToStaticMarkup(<MetricCards metrics={[{ label: "Active sessions", value: 3 }]} />)).toContain("Active sessions");
  });
  it("discloses unsupported FaceDetector behaviour", () => {
    const markup = renderToStaticMarkup(<FeatureCapability label="FaceDetector" supported={false} fallback="camera and tab monitoring remain active" />);
    expect(markup).toContain("Unavailable");
    expect(markup).toContain("camera and tab monitoring remain active");
  });
});

describe("operational interaction rules", () => {
  it("requires distinct primary and secondary cameras", () => expect(validateCameraPair("camera-1", "camera-1")).toContain("different physical devices"));
  it("requires reviewer rationale", () => expect(validateReviewerDecision("CONTINUE", "   ")).toContain("rationale"));
  it("keeps the demonstration timer stable from persisted start time", () => expect(formatElapsed("2026-07-20T10:00:00Z", Date.parse("2026-07-20T11:02:03Z"))).toBe("01:02:03"));
  it("treats a timezone-naive persisted timestamp as UTC", () => expect(formatElapsed("2026-07-20T10:00:00", Date.parse("2026-07-20T11:02:03Z"))).toBe("01:02:03"));
  it("preserves rendered reviewer detail during polling and refresh failures", () => {
    expect(reviewerDetailPresentation(true, true, "")).toBe("content");
    expect(reviewerDetailPresentation(true, false, "Refresh failed")).toBe("content");
    expect(reviewerDetailPresentation(false, true, "")).toBe("loading");
    expect(reviewerDetailPresentation(false, false, "Initial request failed")).toBe("error");
  });
});
