"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import { EmptyState, ErrorState, LoadingState, MetricCards, StatusBadge } from "../../components/OperationalStates";
import { assignCandidateToExamination, assignCourseCohort, createAdministrativeCourse, createAdministrativeExamination, fetchAdminMetrics, fetchAdminPolicy, fetchAdministrativeCandidates, fetchAdministrativeCourses, fetchAdministrativeExaminations, fetchRegistrations, fetchReviewerQueue, previewCourseCohort, registerCandidateForCourse, type AdministrativeCandidate, type AdministrativeCourse, type AdministrativeExamination, type CohortPreview } from "../../lib/api";
import { cohortConfirmation, confirmCohortAndRefresh, errorFeedback, initialAdminDisclosureState, runMutationWithRefresh, successFeedback, toggleAdminDisclosure, type OperationFeedback } from "../../lib/adminManagement";
import type { AdministratorMetrics, InstitutionalPolicy, RegistrationRequest, ReviewerQueueItem } from "../../lib/contracts";

function Feedback({ value }: { value: OperationFeedback }) {
  if (!value) return null;
  return <p className={`form-note ${value.tone === "error" ? "error-text" : "success-text"}`} role={value.tone === "error" ? "alert" : "status"}>{value.message}</p>;
}

export default function AdminPortalPage() {
  const [metrics, setMetrics] = useState<AdministratorMetrics | null>(null);
  const [policy, setPolicy] = useState<InstitutionalPolicy | null>(null);
  const [sessions, setSessions] = useState<ReviewerQueueItem[]>([]);
  const [registrations, setRegistrations] = useState<RegistrationRequest[]>([]);
  const [candidates, setCandidates] = useState<AdministrativeCandidate[]>([]);
  const [examinations, setExaminations] = useState<AdministrativeExamination[]>([]);
  const [courses, setCourses] = useState<AdministrativeCourse[]>([]);
  const [examForm, setExamForm] = useState({ exam_code: "", title: "", duration_minutes: 120, status: "published" as "draft" | "published" | "active" | "inactive", monitoring_mode: "A" as "A" | "B" | "C", is_active: true, policy_profile: "generic" });
  const [courseForm, setCourseForm] = useState({ course_code: "", title: "" });
  const [courseId, setCourseId] = useState("");
  const [courseCandidateId, setCourseCandidateId] = useState("");
  const [cohortExaminationId, setCohortExaminationId] = useState("");
  const [cohortPreview, setCohortPreview] = useState<CohortPreview | null>(null);
  const [disclosure, setDisclosure] = useState(initialAdminDisclosureState);
  const [examinationFeedback, setExaminationFeedback] = useState<OperationFeedback>(null);
  const [courseFeedback, setCourseFeedback] = useState<OperationFeedback>(null);
  const [registrationFeedback, setRegistrationFeedback] = useState<OperationFeedback>(null);
  const [cohortFeedback, setCohortFeedback] = useState<OperationFeedback>(null);
  const [candidateId, setCandidateId] = useState("");
  const [examinationId, setExaminationId] = useState("");
  const [assignmentFeedback, setAssignmentFeedback] = useState<OperationFeedback>(null);
  const [assigning, setAssigning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [metricData, policyData, sessionData, registrationData, candidateData, examinationData, courseData] = await Promise.all([fetchAdminMetrics(), fetchAdminPolicy(), fetchReviewerQueue(), fetchRegistrations(), fetchAdministrativeCandidates(), fetchAdministrativeExaminations(), fetchAdministrativeCourses()]);
      setMetrics(metricData); setPolicy(policyData); setSessions(sessionData); setRegistrations(registrationData); setCandidates(candidateData); setExaminations(examinationData); setCourses(courseData); setUpdatedAt(metricData.last_updated_at ?? new Date().toISOString()); setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Administrator oversight unavailable."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(task); }, [load]);
  async function assignExamination() {
    if (!candidateId || !examinationId) return;
    setAssigning(true); setAssignmentFeedback(null);
    try {
      const assignment = await runMutationWithRefresh(() => assignCandidateToExamination(candidateId, examinationId), load);
      const exam = examinations.find((item) => item.examination_id === examinationId);
      setAssignmentFeedback(successFeedback(`Examination ${exam?.exam_code ?? examinationId} assigned successfully.`));
    } catch (reason) { setAssignmentFeedback(errorFeedback(reason, "Assignment could not be created.")); }
    finally { setAssigning(false); }
  }
  async function createExamination() {
    setExaminationFeedback(null);
    try { const exam = await runMutationWithRefresh(() => createAdministrativeExamination(examForm), load); setExaminationFeedback(successFeedback(`Examination ${exam.exam_code} created successfully.`)); setExamForm({ ...examForm, exam_code: "", title: "" }); }
    catch (reason) { setExaminationFeedback(errorFeedback(reason, "Examination could not be created.")); }
  }
  async function createCourse() {
    setCourseFeedback(null);
    try { const course = await runMutationWithRefresh(() => createAdministrativeCourse({ ...courseForm, is_active: true }), load); setCourseFeedback(successFeedback(`Course ${course.course_code} created successfully.`)); setCourseForm({ course_code: "", title: "" }); }
    catch (reason) { setCourseFeedback(errorFeedback(reason, "Course could not be created.")); }
  }
  async function addCourseRegistration() {
    if (!courseId || !courseCandidateId) return;
    setRegistrationFeedback(null);
    try { await runMutationWithRefresh(() => registerCandidateForCourse(courseId, courseCandidateId), load); const course = courses.find((item) => item.course_id === courseId); const candidate = candidates.find((item) => item.candidate_id === courseCandidateId); setRegistrationFeedback(successFeedback(`${candidate?.full_name ?? "Candidate"} registered for ${course?.course_code ?? "course"} successfully.`)); setCohortPreview(null); }
    catch (reason) { setRegistrationFeedback(errorFeedback(reason, "Course registration failed.")); }
  }
  async function previewCohort() {
    if (!courseId || !cohortExaminationId) return;
    setCohortFeedback(null);
    try { const preview = await previewCourseCohort(courseId, cohortExaminationId); setCohortPreview(preview); setCohortFeedback(successFeedback(`Preview resolved: ${preview.eligible_count} eligible, ${preview.already_assigned_count} already assigned, ${preview.ineligible_count} ineligible.`)); }
    catch (reason) { setCohortFeedback(errorFeedback(reason, "Cohort preview failed.")); }
  }
  async function confirmCohortAssignment() {
    if (!courseId || !cohortExaminationId || !cohortPreview) return;
    setCohortFeedback(null);
    try { const { result, refreshed } = await confirmCohortAndRefresh(courseId, cohortExaminationId, assignCourseCohort, previewCourseCohort); setCohortPreview(refreshed); setCohortFeedback(successFeedback(`${result.created_count} eligible candidate assignment(s) created successfully; duplicates and ineligible candidates were unchanged.`)); await load(); }
    catch (reason) { setCohortFeedback(errorFeedback(reason, "Cohort assignment failed.")); }
  }
  const confirmation = cohortConfirmation(cohortPreview);

  return <PortalShell allowedRoles={["Administrator", "System Administrator"]} title="Administrator Oversight" badge="Institution operations" summary="Institution-scoped identity, session, risk, camera-metadata and audit oversight without reviewer decision authority.">
    <div className="refresh-strip"><span>{updatedAt ? `Last updated ${new Date(updatedAt).toLocaleTimeString()}` : "Awaiting live data"}</span><button type="button" title="Refresh administrator state" onClick={() => void load()} disabled={loading}>Refresh</button></div>
    {loading && !metrics ? <LoadingState label="Loading institution metrics..." /> : error || !metrics ? <ErrorState message={error || "Metrics unavailable."} onRetry={() => void load()} /> : <>
      <MetricCards metrics={[{ label: "Active candidates", value: metrics.active_candidates }, { label: "Active sessions", value: metrics.active_sessions }, { label: "Completed sessions", value: metrics.completed_sessions }, { label: "Unresolved cases", value: metrics.unresolved_reviewer_cases }, { label: "Primary cameras connected", value: metrics.connected_primary_cameras }, { label: "Secondary cameras connected", value: metrics.connected_secondary_cameras }, { label: "Camera failures", value: metrics.camera_failure_count }]} />
      <section className="card"><div className="section-heading"><div><span className="badge">Examination management</span><h2>Institution-controlled examinations</h2></div><button type="button" aria-expanded={disclosure.examination} aria-controls="create-examination-form" onClick={() => setDisclosure((current) => toggleAdminDisclosure(current, "examination"))}>{disclosure.examination ? "Close creation form" : "Create examination"}</button></div><Feedback value={examinationFeedback} />{disclosure.examination && <div id="create-examination-form"><div className="two-column"><label>Examination code<input value={examForm.exam_code} onChange={(event) => setExamForm({ ...examForm, exam_code: event.target.value })} /></label><label>Title<input value={examForm.title} onChange={(event) => setExamForm({ ...examForm, title: event.target.value })} /></label><label>Duration (minutes)<input type="number" min="1" max="1440" value={examForm.duration_minutes} onChange={(event) => setExamForm({ ...examForm, duration_minutes: Number(event.target.value) })} /></label><label>Monitoring mode<select value={examForm.monitoring_mode} onChange={(event) => setExamForm({ ...examForm, monitoring_mode: event.target.value as "A" | "B" | "C" })}><option value="A">Mode A — primary camera</option><option value="B">Mode B — distinct primary and environmental cameras</option><option value="C">Mode C — primary camera with mirror-arrangement attestation</option></select></label><label>Status<select value={examForm.status} onChange={(event) => setExamForm({ ...examForm, status: event.target.value as typeof examForm.status })}><option value="draft">Draft</option><option value="published">Published</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label><label>Policy profile<input value="generic" readOnly aria-readonly="true" /><span className="form-note">Generic is the only implemented profile label. Governance uses the institution&apos;s active persisted IPIME policy, currently shown in Institutional policy below.</span></label></div><label><input type="checkbox" checked={examForm.is_active} onChange={(event) => setExamForm({ ...examForm, is_active: event.target.checked })} /> Examination enabled for institutional use</label><button type="button" className="primary-action" disabled={!examForm.exam_code.trim() || !examForm.title.trim()} onClick={() => void createExamination()}>Create examination</button></div>}</section>
      <section className="card"><div className="section-heading"><div><span className="badge">Examination assignment</span><h2>Assign an enrolled candidate</h2></div></div><div className="two-column"><label>Active candidate<select value={candidateId} onChange={(event) => setCandidateId(event.target.value)}><option value="">Select candidate</option>{candidates.map((candidate) => <option key={candidate.candidate_id} value={candidate.candidate_id}>{candidate.full_name} · {candidate.email}</option>)}</select></label><label>Active examination and monitoring mode<select value={examinationId} onChange={(event) => setExaminationId(event.target.value)}><option value="">Select examination</option>{examinations.filter((exam) => exam.is_active && ["published", "active"].includes(exam.status)).map((exam) => <option key={exam.examination_id} value={exam.examination_id}>{exam.exam_code} · {exam.title} · Mode {exam.monitoring_mode}</option>)}</select></label></div><button type="button" className="primary-action" disabled={assigning || !candidateId || !examinationId} onClick={() => void assignExamination()}>{assigning ? "Assigning..." : "Assign examination"}</button><Feedback value={assignmentFeedback} /></section>
      <section className="card"><div className="section-heading"><div><span className="badge">Course cohort assignment</span><h2>Resolve, preview and confirm a registered cohort</h2></div><div className="row-actions"><button type="button" aria-expanded={disclosure.course} aria-controls="create-course-form" onClick={() => setDisclosure((current) => toggleAdminDisclosure(current, "course"))}>{disclosure.course ? "Close course form" : "Create course"}</button><button type="button" aria-expanded={disclosure.registration} aria-controls="course-registration-form" onClick={() => setDisclosure((current) => toggleAdminDisclosure(current, "registration"))}>{disclosure.registration ? "Close registration form" : "Register candidate"}</button></div></div><Feedback value={courseFeedback} /><Feedback value={registrationFeedback} />{disclosure.course && <div id="create-course-form"><div className="two-column"><label>New course code<input value={courseForm.course_code} onChange={(event) => setCourseForm({ ...courseForm, course_code: event.target.value })} /></label><label>New course title<input value={courseForm.title} onChange={(event) => setCourseForm({ ...courseForm, title: event.target.value })} /></label></div><button type="button" disabled={!courseForm.course_code.trim() || !courseForm.title.trim()} onClick={() => void createCourse()}>Create course</button></div>}<label>Course<select value={courseId} onChange={(event) => { setCourseId(event.target.value); setCohortPreview(null); setCohortFeedback(null); }}><option value="">Select course</option>{courses.filter((course) => course.is_active).map((course) => <option key={course.course_id} value={course.course_id}>{course.course_code} · {course.title}</option>)}</select></label>{disclosure.registration && <div id="course-registration-form"><label>Register candidate<select value={courseCandidateId} onChange={(event) => setCourseCandidateId(event.target.value)}><option value="">Select enrolled candidate</option>{candidates.map((candidate) => <option key={candidate.candidate_id} value={candidate.candidate_id}>{candidate.full_name} · {candidate.email}</option>)}</select></label><button type="button" disabled={!courseId || !courseCandidateId} onClick={() => void addCourseRegistration()}>Add course registration</button></div>}<label>Examination for cohort<select value={cohortExaminationId} onChange={(event) => { setCohortExaminationId(event.target.value); setCohortPreview(null); setCohortFeedback(null); }}><option value="">Select active examination</option>{examinations.filter((exam) => exam.is_active && ["published", "active"].includes(exam.status)).map((exam) => <option key={exam.examination_id} value={exam.examination_id}>{exam.exam_code} · Mode {exam.monitoring_mode}</option>)}</select></label><button type="button" disabled={!courseId || !cohortExaminationId} onClick={() => void previewCohort()}>Preview eligible cohort</button>{cohortPreview && <><p><strong>Preview:</strong> {cohortPreview.eligible_count} eligible · {cohortPreview.already_assigned_count} already assigned · {cohortPreview.ineligible_count} ineligible · Mode {cohortPreview.monitoring_mode}</p><div className="oversight-table">{cohortPreview.candidates.map((candidate) => <div className="oversight-row" key={candidate.candidate_id}><div><strong>{candidate.full_name}</strong><span>{candidate.email}</span></div><StatusBadge label={candidate.outcome.replaceAll("_", " ")} tone={candidate.outcome === "eligible" ? "success" : candidate.outcome === "ineligible" ? "danger" : "warning"} /><span>{candidate.reason ?? "Eligible for assignment"}</span></div>)}</div><button type="button" className="primary-action" disabled={confirmation.disabled} onClick={() => void confirmCohortAssignment()}>{confirmation.label}</button>{confirmation.explanation && <p className="form-note" role="status">{confirmation.explanation}</p>}</>}<Feedback value={cohortFeedback} /></section>
      <section className="card"><div className="section-heading"><div><span className="badge">Registration lifecycle</span><h2>Institution identity status</h2></div><StatusBadge label={`${registrations.filter((item) => item.status === "pending_approval").length} pending approval`} tone={registrations.some((item) => item.status === "pending_approval") ? "warning" : "neutral"} /></div>{registrations.length ? <div className="oversight-table" role="table" aria-label="Registration lifecycle">{registrations.map((item) => <div className="oversight-row" role="row" key={item.registration_id}><div role="cell"><strong>{item.email}</strong><span>{item.account_type}</span></div><div role="cell">Account: {item.status.replaceAll("_", " ")}</div><div role="cell">Verification: {item.prototype_verified ? "prototype verified" : "pending"}</div><StatusBadge label={item.status.replaceAll("_", " ")} tone={item.status === "active" ? "success" : item.status === "rejected" ? "danger" : "warning"} /></div>)}</div> : <EmptyState title="No registration requests" detail="No institution-scoped registration lifecycle records are available." />}</section>
      <section className="risk-metric-grid">{Object.entries(metrics.risk_counts).map(([level, count]) => <article className={`metric-card risk-${level.toLowerCase()}`} key={level}><span>{level} risk sessions</span><strong>{count}</strong></article>)}</section>
      <section className="two-column"><article className="card"><span className="badge">Institutional policy</span><h2>{policy ? `Version ${policy.policy_version}` : "Unavailable"}</h2>{policy ? <dl className="detail-list"><div><dt>Reviewer threshold</dt><dd>{policy.reviewer_notification_threshold}</dd></div><div><dt>Reauthentication threshold</dt><dd>{policy.reauthentication_threshold}</dd></div><div><dt>Candidate acknowledgement</dt><dd>{policy.candidate_acknowledgement_required ? "Required" : "Not required"}</dd></div><div><dt>Automatic termination</dt><dd>{policy.automatic_exam_termination_allowed ? "Enabled" : "Disabled"}</dd></div></dl> : <p>No active persisted policy exists yet.</p>}</article><article className="card"><span className="badge">Recent audit</span><h2>Governance activity</h2>{metrics.recent_audit_activity.length ? <ul className="compact-list">{metrics.recent_audit_activity.map((item) => <li key={String(item.audit_id)}><strong>{String(item.action)}</strong><span>{new Date(String(item.timestamp)).toLocaleString()}</span></li>)}</ul> : <p>No governance audit activity exists.</p>}</article></section>
      <section className="card"><div className="section-heading"><div><span className="badge">Session oversight</span><h2>Dual-camera operational sessions</h2></div><StatusBadge label={`${sessions.length} sessions`} /></div>{sessions.length ? <div className="oversight-table" role="table" aria-label="Administrator session oversight">{sessions.map((session) => <div className="oversight-row" role="row" key={session.session_id}><div role="cell"><strong>{session.candidate_name}</strong><span>{session.examination}</span></div><div role="cell">Risk: {session.latest_risk_level ?? "Unavailable"}</div><div role="cell">Primary: {session.primary_camera_status}</div><div role="cell">Secondary: {session.secondary_camera_status}</div><Link className="button-link" href={`/admin/sessions/${session.session_id}`}>Inspect</Link></div>)}</div> : <EmptyState title="No sessions" detail="No institution-scoped examination sessions are available." />}</section>
    </>}
  </PortalShell>;
}
