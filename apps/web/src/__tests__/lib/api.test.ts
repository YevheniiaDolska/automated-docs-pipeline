import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { setToken, getToken, ApiError } from "@/lib/api";

describe("Token management", () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset module-level _token by setting null
    setToken(null);
  });

  it("setToken stores token in localStorage as veridoc_token", () => {
    setToken("abc123");
    expect(localStorage.getItem("veridoc_token")).toBe("abc123");
  });

  it("setToken(null) removes token from localStorage", () => {
    setToken("abc123");
    setToken(null);
    expect(localStorage.getItem("veridoc_token")).toBeNull();
  });

  it("getToken reads from localStorage on first call", () => {
    localStorage.setItem("veridoc_token", "stored-token");
    // Reset the in-memory cache
    setToken(null);
    localStorage.setItem("veridoc_token", "stored-token");
    expect(getToken()).toBe("stored-token");
  });

  it("getToken returns cached token on subsequent calls", () => {
    setToken("cached-token");
    // Even if localStorage is cleared, in-memory cache should return
    localStorage.clear();
    expect(getToken()).toBe("cached-token");
  });
});

describe("ApiError", () => {
  it("has correct name", () => {
    const err = new ApiError(401, "Unauthorized");
    expect(err.name).toBe("ApiError");
  });

  it("has correct status and message", () => {
    const err = new ApiError(404, "Not found");
    expect(err.status).toBe(404);
    expect(err.message).toBe("Not found");
  });

  it("is an instance of Error", () => {
    const err = new ApiError(500, "Server error");
    expect(err).toBeInstanceOf(Error);
  });
});

describe("API helpers (fetch integration)", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
    setToken(null);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("auth.login calls POST /auth/login and stores token", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: "new-jwt-token" }),
    });

    // Import dynamically to get fresh module with mocked fetch
    const { auth } = await import("@/lib/api");
    const result = await auth.login({ email: "a@b.com", password: "pass" });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/login"),
      expect.objectContaining({ method: "POST" }),
    );
    expect(result.access_token).toBe("new-jwt-token");
    expect(localStorage.getItem("veridoc_token")).toBe("new-jwt-token");
  });

  it("auth.register calls POST /auth/register", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, email: "a@b.com" }),
    });

    const { auth } = await import("@/lib/api");
    const result = await auth.register({ email: "a@b.com", password: "pass" });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/register"),
      expect.objectContaining({ method: "POST" }),
    );
    expect(result.email).toBe("a@b.com");
  });

  it("billing.getUsage calls GET /billing/usage", async () => {
    setToken("test-token");
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          tier: "pro",
          status: "active",
          ai_requests_used: 50,
          ai_requests_limit: 500,
          pages_generated: 10,
          pages_limit: 100,
          api_calls_used: 5,
          api_calls_limit: 50,
          current_period_end: "2026-04-15T00:00:00Z",
        }),
    });

    const { billing } = await import("@/lib/api");
    const usage = await billing.getUsage();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/billing/usage"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      }),
    );
    expect(usage.tier).toBe("pro");
  });

  it("throws ApiError on non-ok response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "Invalid token" }),
    });

    const { auth } = await import("@/lib/api");
    await expect(auth.me()).rejects.toThrow("Invalid token");
  });

  it("includes Authorization header when token is set", async () => {
    setToken("bearer-test");
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ email: "test@test.com" }),
    });

    const { auth } = await import("@/lib/api");
    await auth.me();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer bearer-test",
        }),
      }),
    );
  });
});
