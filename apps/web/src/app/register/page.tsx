"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { fetchRegistrationInstitutions, registerIdentity, resumeEnrollment } from "../../lib/api";
import type { InstitutionRegistration, RegistrationField } from "../../lib/contracts";
import { defaultRecoveryInstitution, recoveryCredentialsReady } from "../../lib/enrolmentRecovery";

type AccountType = "candidate" | "reviewer" | "administrator";

function ConfiguredField({ field }: { field: RegistrationField }) {
  const common = { name: `configured.${field.name}`, required: field.required, title: field.help_text || undefined };
  return <label>{field.label}
    {field.type === "select" ? <select {...common} defaultValue=""><option value="" disabled>{field.placeholder || `Select ${field.label.toLowerCase()}`}</option>{field.options.map((option) => <option key={option}>{option}</option>)}</select>
      : field.type === "checkbox" ? <span className="consent-check"><input {...common} type="checkbox" /><span>{field.help_text || field.label}</span></span>
      : <input {...common} type={field.type} placeholder={field.placeholder} pattern={field.pattern ?? undefined} />}
    {field.type !== "checkbox" && field.help_text && <span className="field-help">{field.help_text}</span>}
  </label>;
}

export default function RegistrationPage() {
  const [accountType, setAccountType] = useState<AccountType>("candidate");
  const [institutions, setInstitutions] = useState<InstitutionRegistration[]>([]);
  const [institutionCode, setInstitutionCode] = useState("");
  const [status, setStatus] = useState("Loading active institution registration configurations...");
  const [busy, setBusy] = useState(false);
  const [showResume, setShowResume] = useState(false);
  const [resumeEmail, setResumeEmail] = useState("");
  const [resumePassword, setResumePassword] = useState("");
  const [resumeInstitutionCode, setResumeInstitutionCode] = useState("");
  const [resumeStatus, setResumeStatus] = useState("");
  const selected = institutions.find((item) => item.code === institutionCode);
  const fields = useMemo(() => (selected?.fields ?? []).filter((field) => field.active && field.applies_to.includes(accountType)).sort((a, b) => a.order - b.order), [selected, accountType]);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("type");
    const resumeRequested = new URLSearchParams(window.location.search).get("resume") === "1";
    const initialise = window.setTimeout(() => {
      if (requested === "candidate" || requested === "reviewer" || requested === "administrator") setAccountType(requested);
      if (resumeRequested) setShowResume(true);
    }, 0);
    const controller = new AbortController();
    fetchRegistrationInstitutions(controller.signal).then((items) => {
      setInstitutions(items);
      setResumeInstitutionCode(defaultRecoveryInstitution(items.map((item) => item.code)));
      setStatus("Select an institution to load its current registration requirements.");
    }).catch((error) => setStatus(error instanceof Error ? error.message : "Institution configuration is unavailable."));
    return () => { window.clearTimeout(initialise); controller.abort(); };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    setBusy(true); setStatus("Validating the current institution configuration...");
    const form = new FormData(event.currentTarget); const configured_fields: Record<string, unknown> = {};
    for (const field of fields) configured_fields[field.name] = field.type === "checkbox" ? form.get(`configured.${field.name}`) === "on" : String(form.get(`configured.${field.name}`) ?? "");
    try {
      const email = String(configured_fields.contact_email ?? form.get("email") ?? "");
      const fullName = String(configured_fields.full_name ?? form.get("full_name") ?? "");
      const candidateIdentifier = selected.candidate_identifier_field ? String(configured_fields[selected.candidate_identifier_field] ?? "") : null;
      const result = await registerIdentity({ institution_code: selected.code, configuration_version: selected.version, configured_fields, account_type: accountType, candidate_identifier: accountType === "candidate" ? candidateIdentifier : null, full_name: fullName, email, password: String(form.get("password")), confirm_password: String(form.get("confirm_password")), biometric_consent: accountType === "candidate" && form.get("biometric_consent") === "on" });
      if (accountType === "candidate" && result.enrollment_token) { sessionStorage.setItem("serps_enrollment_token", result.enrollment_token); sessionStorage.setItem("serps_enrollment_actions", JSON.stringify(result.required_actions)); window.location.href = "/enrolment"; return; }
      setStatus("Registration request recorded. A System Administrator must approve this account before sign-in."); event.currentTarget.reset(); setInstitutionCode("");
    } catch (error) { setStatus(error instanceof Error ? error.message : "Registration failed."); } finally { setBusy(false); }
  }

  async function resume(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!recoveryCredentialsReady(resumeEmail, resumePassword)) {
      setResumeStatus("Enter the email and password used for the incomplete registration.");
      return;
    }
    setBusy(true); setResumeStatus("Recovering the pending facial-enrolment session...");
    try {
      const result = await resumeEnrollment({ ...(resumeInstitutionCode ? { institution_code: resumeInstitutionCode } : {}), email: resumeEmail.trim(), password: resumePassword });
      sessionStorage.setItem("serps_enrollment_token", result.challenge_token);
      sessionStorage.setItem("serps_enrollment_actions", JSON.stringify(result.required_actions));
      window.location.href = "/enrolment";
    } catch (error) { setResumeStatus(error instanceof Error ? error.message : "Pending enrolment could not be resumed."); }
    finally { setBusy(false); }
  }

  return <main className="page-shell compact-shell"><section className="auth-layout">
    <div className="hero auth-hero"><p className="eyebrow">Controlled identity lifecycle</p><h1>Request a SERPS account</h1><p>Registration requirements are supplied by the selected institution and validated again by Application Services.</p><Link className="hero-link" href="/login">Already registered? Sign in</Link></div>
    <form className="card auth-card" onSubmit={submit}><span className="badge">Registration</span>
      <div className="account-type-tabs" role="tablist" aria-label="Account type">{(["candidate", "reviewer", "administrator"] as AccountType[]).map((type) => <button type="button" role="tab" aria-selected={accountType === type} className={accountType === type ? "active" : ""} onClick={() => setAccountType(type)} key={type}>{type}</button>)}</div>
      <label>Institution<select aria-label="Institution" value={institutionCode} onChange={(event) => setInstitutionCode(event.target.value)} required><option value="" disabled>Select institution</option>{institutions.map((item) => <option value={item.code} key={item.code}>{item.name}</option>)}</select></label>
      {selected && <p className="field-help">Configuration version {selected.version} · {selected.code}</p>}
      {fields.map((field) => <ConfiguredField field={field} key={field.name} />)}
      {selected && <><label>Create password<input name="password" type="password" minLength={12} autoComplete="new-password" required /></label><label>Confirm password<input name="confirm_password" type="password" minLength={12} autoComplete="new-password" required /></label></>}
      {selected && accountType === "candidate" && <label className="consent-check"><input name="biometric_consent" type="checkbox" required /><span>I consent to processing a derived facial representation for this research-prototype identity workflow. Raw images and video will not be stored.</span></label>}
      <button type="submit" disabled={busy || !selected}>{busy ? "Submitting..." : accountType === "candidate" ? "Verify and continue" : "Submit approval request"}</button><p className="form-note" role="status">{status}</p>
    </form>
    <section className="card auth-card resume-enrolment-entry" aria-label="Incomplete enrolment recovery">
      <button type="button" className="secondary-action" aria-expanded={showResume} aria-controls="resume-enrolment-form" onClick={() => setShowResume((value) => !value)}>{showResume ? "Hide enrolment recovery" : "Resume enrolment"}</button>
      {showResume && <form id="resume-enrolment-form" onSubmit={resume}><span className="badge">Incomplete registration</span><h2>Continue an incomplete candidate registration</h2><p>Use the same email and password. The identity service securely resolves the institution from the pending account; no registration form selection is required.</p><label>Email<input type="email" autoComplete="email" value={resumeEmail} onChange={(event) => setResumeEmail(event.target.value)} required /></label><label>Password<input type="password" autoComplete="current-password" minLength={12} value={resumePassword} onChange={(event) => setResumePassword(event.target.value)} required /></label><button type="submit" disabled={busy || !recoveryCredentialsReady(resumeEmail, resumePassword)}>{busy ? "Recovering enrolment..." : "Resume facial enrolment"}</button>{resumeStatus && <p className="form-note" role="status">{resumeStatus}</p>}</form>}
    </section>
  </section></main>;
}
