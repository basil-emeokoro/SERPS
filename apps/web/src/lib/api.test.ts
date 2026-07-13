import { describe, expect, it } from "vitest";
import { getApiBaseUrl } from "./api";

describe("API client configuration", () => {
  it("falls back to the local FastAPI endpoint", () => {
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });
});
