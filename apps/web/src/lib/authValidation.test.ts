import { describe, expect, it } from "vitest";
import { validateLogin } from "./authValidation";

describe("login validation", () => {
  it("reports each missing or invalid field specifically", () => {
    expect(validateLogin({ institutionCode: "", email: "person@example.com", password: "secret" })).toBe("Enter your institution code.");
    expect(validateLogin({ institutionCode: "MIVA", email: "bad", password: "secret" })).toBe("Enter a valid email address.");
    expect(validateLogin({ institutionCode: "MIVA", email: "person@example.com", password: "" })).toBe("Enter your password.");
  });
  it("accepts syntactically valid complete fields", () => expect(validateLogin({ institutionCode: "MIVA", email: "person@example.com", password: "secret" })).toBeNull());
});
