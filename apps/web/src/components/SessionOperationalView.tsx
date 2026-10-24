import type { OperationalSessionDetail } from "../lib/contracts";
import { CameraPanel, EmptyState, RiskIndicator, StatusBadge } from "./OperationalStates";

function text(value: unknown): string { return value == null ? "Unavailable" : String(value); }

const timelineLabels: Record<string, string> = {
  camera_connected: "camera connected", camera_disconnected: "camera disconnected", camera_reconnected: "camera reconnected",
  camera_heartbeat: "camera heartbeat received", face_not_detected: "face not detected", face_detected: "face detected", sustained_face_absence: "sustained face absence", face_detector_unavailable: "face detector unavailable",
  person_detected: "person detected", multiple_persons_detected: "multiple persons detected",
  mobile_phone_detected: "mobile phone detected", object_detector_unavailable: "object detector unavailable",
  microphone_connected: "microphone connected", microphone_disconnected: "microphone disconnected",
  audio_activity_detected: "audio activity detected", sustained_audio_activity: "sustained audio activity detected",
  audio_monitor_unavailable: "audio monitor unavailable", tab_focus_lost: "assessment tab lost focus",
  ContextualAssessment: "Contextual risk assessed", AgentRecommendation: "Operational recommendation created",
  PolicyEvaluation: "Institutional policy evaluated", ReviewerDecision: "Human reviewer decision recorded",
  EvidenceEvent: "Evidence recorded",
};

function timelineText(entry: OperationalSessionDetail["timeline"][number]): string {
  const event = text(entry.payload.event_type ?? entry.payload.action ?? entry.payload.decision ?? entry.entry_type);
  const camera = entry.payload.camera_id ? `${String(entry.payload.camera_id)} ` : "";
  return timelineLabels[event] ?? timelineLabels[entry.entry_type] ?? `${camera}${event.replaceAll("_", " ")}`;
}

function metadataRows(entry: OperationalSessionDetail["timeline"][number]) {
  const metadata = entry.payload.metadata_json;
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) return null;
  const values = metadata as Record<string, unknown>;
  const candidates: Array<[string, unknown]> = [
    ["Detector / model", values.model_name ?? values.detector_name],
    ["Model / detector version", values.model_version ?? values.detector_version],
    ["Detected class", values.detected_class],
    ["Object count", values.object_count],
    ["Recurrence", values.recurrence_count],
    ["Threshold", values.threshold],
    ["Duration (ms)", values.duration_ms],
    ["Normalised level", values.normalized_level],
    ["Correlation window (s)", values.correlation_window_seconds],
  ];
  const rows = candidates.filter(([, value]) => value != null);
  return rows.map(([label, value]) => <div key={String(label)}><dt>{label}</dt><dd>{text(value)}</dd></div>);
}

export function SessionOperationalView({ detail }: { detail: OperationalSessionDetail }) {
  const assessment = detail.latest_assessment;
  return <>
    <section className="card identity-assurance-card">
      <div className="section-heading"><div><span className="badge">Identity assurance</span><h2>Privacy-safe verification status</h2></div><StatusBadge label={detail.identity_assurance.authentication_result.replaceAll("_", " ")} tone={detail.identity_assurance.authentication_result === "verified" || detail.identity_assurance.demo_bypass ? "success" : "warning"} /></div>
      <dl className="detail-list"><div><dt>Facial enrolment</dt><dd>{detail.identity_assurance.enrolment_status.replaceAll("_", " ")}</dd></div><div><dt>Liveness result</dt><dd>{detail.identity_assurance.liveness_result.replaceAll("_", " ")}</dd></div><div><dt>Identity confidence</dt><dd>{detail.identity_assurance.identity_confidence == null ? "Not available" : `${Math.round(detail.identity_assurance.identity_confidence * 100)}%`}</dd></div><div><dt>Last verified</dt><dd>{detail.identity_assurance.last_verified_at ? new Date(detail.identity_assurance.last_verified_at).toLocaleString() : "Not recorded"}</dd></div></dl>
      <p className="privacy-note">No raw biometric image, video, facial descriptor or audio recording is exposed to reviewers.</p>
    </section>
    <section className="session-summary card"><div><span className="eyebrow dark">Operational session</span><h2>{text(detail.candidate.full_name)} · {text(detail.examination.title)}</h2><p>{text(detail.institution.name)} · Session {text(detail.session.session_id)} · Mode {text(detail.session.deployment_mode)}</p></div><StatusBadge label={text(detail.session.status)} tone={detail.session.status === "active" ? "success" : "neutral"} /></section>
    <section className="dual-camera-grid" aria-label="Primary and secondary camera status"><CameraPanel title="Primary camera" camera={detail.primary_camera} /><CameraPanel title="Secondary camera" camera={detail.secondary_camera} /></section>
    <section className="governance-grid">
      <article className="card"><span className="badge">Contextual intelligence</span><h2>Risk assessment</h2><RiskIndicator level={assessment ? text(assessment.risk_level) : null} score={assessment && typeof assessment.risk_score === "number" ? assessment.risk_score : null} /><p>{assessment ? text(assessment.explanation) : "No contextual assessment is available."}</p></article>
      <article className="card"><span className="badge">Bounded advisory</span><h2>Agentic recommendation</h2><p>{detail.latest_recommendation ? text(detail.latest_recommendation.recommended_action) : "No recommendation available."}</p><p>{detail.latest_recommendation ? text(detail.latest_recommendation.explanation) : "Evidence has not produced a recommendation."}</p></article>
      <article className="card"><span className="badge">Institution policy</span><h2>IPIME outcome</h2><p>{detail.latest_policy_evaluation ? text(detail.latest_policy_evaluation.approved_action) : "No policy evaluation available."}</p><p>{detail.latest_policy_evaluation ? text(detail.latest_policy_evaluation.explanation) : "Policy has not been evaluated."}</p></article>
    </section>
    <section className="card timeline-card">
      <div className="section-heading"><div><span className="badge">Metadata only</span><h2>Evidence and governance timeline</h2></div></div>
      <p>Reviewer evidence contains structured detector metadata and explainable governance output. SERPS does not provide a remote live-media feed.</p>
      {detail.timeline_truncated ? <p className="form-note">Showing the most recent {detail.timeline.length.toLocaleString()} of {detail.timeline_total_entries.toLocaleString()} persisted entries.</p> : null}
      {detail.timeline.length ? <ol className="timeline">{detail.timeline.map((entry) => <li key={`${entry.entry_type}-${entry.entity_id}`}>
        <time>{new Date(entry.timestamp).toLocaleString()}</time><strong>{timelineText(entry)}</strong>
        <details><summary title="Show technical event details">Technical details</summary><dl>
          <div><dt>Record type</dt><dd>{entry.entry_type}</dd></div><div><dt>Identifier</dt><dd>{entry.entity_id}</dd></div>
          <div><dt>Event type</dt><dd>{text(entry.payload.event_type)}</dd></div><div><dt>Source / rule</dt><dd>{text(entry.payload.source_module ?? entry.payload.rule_version ?? entry.payload.policy_version)}</dd></div>
          <div><dt>Camera / microphone source</dt><dd>{text(entry.payload.camera_id ?? (entry.payload.event_type && String(entry.payload.event_type).includes("audio") ? "browser microphone" : null))}</dd></div>
          <div><dt>Confidence</dt><dd>{typeof entry.payload.confidence === "number" ? `${Math.round(entry.payload.confidence * 100)}%` : "Unavailable"}</dd></div>
          {metadataRows(entry)}
        </dl></details>
      </li>)}</ol> : <EmptyState title="No timeline entries" detail="No EvidenceEvents or governance records have been persisted for this session." />}
    </section>
  </>;
}
