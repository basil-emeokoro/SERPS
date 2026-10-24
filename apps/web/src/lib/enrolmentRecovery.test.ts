import { describe, expect, it } from "vitest";
import { defaultRecoveryInstitution, recoveryCredentialsReady } from "./enrolmentRecovery";

describe("incomplete enrolment recovery", () => {
  it("automatically selects the only available institution", () => {
    expect(defaultRecoveryInstitution(["MIVA"])).toBe("MIVA");
    expect(defaultRecoveryInstitution(["MIVA", "OTHER"])).toBe("");
  });
  it("enables recovery only for a tenant and complete credentials", () => {
    expect(recoveryCredentialsReady("candidate@example.test", "Password123!")).toBe(true);
    expect(recoveryCredentialsReady("invalid", "Password123!")).toBe(false);
    expect(recoveryCredentialsReady("candidate@example.test", "short")).toBe(false);
  });
});
