"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ApiError, fetchCurrentUser, login } from "../../lib/api";
import { validateLogin } from "../../lib/authValidation";

const roleDestinations: Record<string, string> = {
  Candidate: "/candidate",
  "Reviewer/Proctor": "/reviewer",
  Administrator: "/admin",
  "System Administrator": "/system-admin",
};

const demonstrationAccounts = new Set([
  "candidate@miva.edu.ng",
  "reviewer@miva.edu.ng",
  "admin@miva.edu.ng",
  "sysadmin@serps.local",
]);

function destinationFor(roles: string[]): string {
  for (const role of ["System Administrator", "Administrator", "Reviewer/Proctor", "Candidate"]) {
    if (roles.includes(role)) {
      return roleDestinations[role];
    }
  }
  return "/";
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [institutionCode, setInstitutionCode] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<string>("Enter your institution and account credentials to continue.");
  const [hasError, setHasError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { const task = window.setTimeout(() => setMounted(true), 0); return () => window.clearTimeout(task); }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedInstitution = institutionCode.trim().toUpperCase();
    const validation = validateLogin({ institutionCode: normalizedInstitution, email: normalizedEmail, password });
    if (validation) {
      setHasError(true);
      setStatus(validation);
      return;
    }
    setBusy(true);
    setHasError(false);
    setStatus("Securely validating your account...");
    try {
      const tokens = await login({ email: normalizedEmail, password, institution_code: normalizedInstitution });
      if (tokens.authentication_stage === "enrollment_required") {
        sessionStorage.setItem("serps_enrollment_token", tokens.challenge_token);
        sessionStorage.setItem("serps_enrollment_actions", JSON.stringify(tokens.required_actions));
        sessionStorage.setItem("serps_enrollment_subject", normalizedEmail);
        sessionStorage.setItem("serps_enrollment_notice", "Your account was recovered. Validated fixed observations were restored where available; dynamic liveness restarts with this fresh challenge.");
        window.location.href = "/enrolment";
        return;
      }
      if (tokens.authentication_stage === "facial_required") {
        sessionStorage.setItem("serps_face_challenge", tokens.challenge_token);
        sessionStorage.setItem("serps_face_actions", JSON.stringify(tokens.required_actions));
        sessionStorage.setItem("serps_face_mode", "authentication");
        window.location.href = "/facial-auth";
        return;
      }
      sessionStorage.setItem("serps_access_token", tokens.access_token);
      sessionStorage.setItem("serps_refresh_token", tokens.refresh_token);
      const user = await fetchCurrentUser(tokens.access_token);
      sessionStorage.setItem("serps_current_user", JSON.stringify(user));
      window.location.href = destinationFor(user.roles);
    } catch (error) {
      setHasError(true);
      setStatus(error instanceof ApiError && (error.status === 401 || error.status === 404) ? "Invalid email or password." : error instanceof Error ? error.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell compact-shell">
      <section className="auth-layout">
        <div className="hero auth-hero">
          <p className="eyebrow">SERPS POP</p>
          <h1>Sign in to SERPS</h1>
          <p>
            Authentication is performed by the SERPS Identity Service. User roles and permissions are securely validated by the
            backend before access to role-specific portals is granted.
          </p>
        </div>

        <form className="card auth-card" onSubmit={onSubmit}>
          <span className="badge">Authentication</span>
          <h2>Account sign in</h2>
          <label>
            Institution code
            <input value={institutionCode} onChange={(event) => setInstitutionCode(event.target.value)} autoComplete="organization" required />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
          </label>
          {mounted && demonstrationAccounts.has(email.trim().toLowerCase()) && <span className="demo-indicator">Demonstration Account</span>}
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button type="submit" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
          <p className={hasError ? "auth-error" : "form-note"} role={hasError ? "alert" : "status"} aria-live="polite">{hasError && <span aria-hidden="true">⚠ </span>}{status}</p>
          <div className="auth-entry-links" aria-label="Registration options">
            <Link href="/register?type=candidate">Candidate registration</Link>
            <Link href="/register?type=candidate&resume=1">Resume enrolment</Link>
            <Link href="/register?type=reviewer">Reviewer registration request</Link>
            <Link href="/register?type=administrator">Administrator registration request</Link>
          </div>
        </form>
      </section>
    </main>
  );
}
