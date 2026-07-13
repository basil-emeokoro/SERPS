import { PortalShell } from "../../components/PortalShell";

export default function SystemAdminPortalPage() {
  return (
    <PortalShell
      allowedRoles={["System Administrator"]}
      title="System Administrator Portal"
      badge="System Administrator"
      summary="System-level administration for institutions, users, roles and audit oversight."
    >
      <section className="status-grid">
        <article className="card">
          <span className="badge">Institutions</span>
          <h2>Institution management</h2>
          <p>Use `/api/v1/institutions` to create and list institution tenants.</p>
        </article>
        <article className="card">
          <span className="badge">Users & Roles</span>
          <h2>Identity administration</h2>
          <p>Use `/api/v1/users` and `/api/v1/roles` for controlled staff and role management.</p>
        </article>
        <article className="card">
          <span className="badge">Audit</span>
          <h2>Security audit</h2>
          <p>Use `/api/v1/audit-logs` to inspect significant security and domain actions.</p>
        </article>
      </section>
    </PortalShell>
  );
}
