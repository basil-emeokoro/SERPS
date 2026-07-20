import Link from "next/link";
import type { MeResponse } from "../lib/contracts";
import { navigationForRoles } from "../lib/operational";

export function RoleNavigation({ user }: { user: MeResponse }) {
  return <nav className="role-navigation" aria-label="Role-aware portal navigation">{navigationForRoles(user.roles).map((link) => <Link href={link.href} key={link.href}>{link.label}</Link>)}</nav>;
}
