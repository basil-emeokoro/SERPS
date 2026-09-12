export function defaultRecoveryInstitution(codes: string[]): string {
  return codes.length === 1 ? codes[0] : "";
}

export function recoveryCredentialsReady(institutionCode: string, email: string, password: string): boolean {
  return !!institutionCode && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) && password.length >= 12;
}
