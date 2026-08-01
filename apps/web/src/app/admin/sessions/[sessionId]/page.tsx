"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { PortalShell } from "../../../../components/PortalShell";
import { ErrorState, LoadingState } from "../../../../components/OperationalStates";
import { SessionOperationalView } from "../../../../components/SessionOperationalView";
import { fetchReviewerSession } from "../../../../lib/api";
import type { OperationalSessionDetail } from "../../../../lib/contracts";

export default function AdministratorSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [detail, setDetail] = useState<OperationalSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => { await Promise.resolve(); setLoading(true); try { setDetail(await fetchReviewerSession(sessionId, "admin")); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Oversight detail unavailable."); } finally { setLoading(false); } }, [sessionId]);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); const poll = window.setInterval(() => void load(), 10000); return () => { window.clearTimeout(task); window.clearInterval(poll); }; }, [load]);
  return <PortalShell allowedRoles={["Administrator", "System Administrator"]} title="Administrator Session Oversight" badge="Read-only oversight" summary="Institution-scoped dual-camera metadata, risk, policy, reviewer state and audit timeline. Administrators cannot submit reviewer decisions here.">{loading ? <LoadingState /> : error || !detail ? <ErrorState message={error || "Session unavailable."} onRetry={() => void load()} /> : <SessionOperationalView detail={detail} />}</PortalShell>;
}
