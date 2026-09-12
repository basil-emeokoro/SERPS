export type LoginFields = { institutionCode: string; email: string; password: string };

export function validateLogin(fields: LoginFields): string | null {
  if (!fields.institutionCode.trim()) return "Enter your institution code.";
  const email = fields.email.trim();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address.";
  if (!fields.password) return "Enter your password.";
  return null;
}
