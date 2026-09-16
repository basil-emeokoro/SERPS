import { describe, expect, it } from "vitest";
import { facialVerificationDestination } from "./facialVerification";

describe("single-observation facial verification redirect", () => {
  it("routes a verified candidate to the candidate portal", () => expect(facialVerificationDestination(["Candidate"])).toBe("/candidate"));
  it("uses the first recognised role and falls back safely", () => {
    expect(facialVerificationDestination(["Unknown", "Administrator"])).toBe("/admin");
    expect(facialVerificationDestination(["Unknown"])).toBe("/");
  });
});
