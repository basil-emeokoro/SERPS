export function defaultRecoveryInstitution(codes: string[]): string {
  return codes.length === 1 ? codes[0] : "";
}

export function recoveryCredentialsReady(email: string, password: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) && password.length >= 12;
}
