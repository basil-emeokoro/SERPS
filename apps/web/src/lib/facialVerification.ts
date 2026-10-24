export const facialVerificationDestinations: Record<string, string> = { Candidate: "/candidate", "Reviewer/Proctor": "/reviewer", Administrator: "/admin", "System Administrator": "/system-admin" };

export function facialVerificationDestination(roles: string[]): string {
  return roles.map((role) => facialVerificationDestinations[role]).find(Boolean) ?? "/";
}
