import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "./client";

function jsonResponse(body: unknown, status = 200, contentType = "application/json") {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": contentType },
  });
}

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed data on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ status: "ok" })));

    await expect(apiFetch<{ status: string }>("/api/health")).resolves.toEqual({ status: "ok" });
  });

  it("turns a problem+json response into an ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ code: "not_found", detail: "Not Found" }, 404, "application/problem+json"),
        ),
    );

    await expect(apiFetch("/api/nope")).rejects.toMatchObject({
      status: 404,
      code: "not_found",
      detail: "Not Found",
    });
    await expect(apiFetch("/api/nope")).rejects.toBeInstanceOf(ApiError);
  });

  it("uses a generic ApiError when the error body is not problem+json", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("plain text failure", {
          status: 500,
          headers: { "content-type": "text/plain" },
        }),
      ),
    );

    await expect(apiFetch("/api/broken")).rejects.toMatchObject({
      status: 500,
      code: "failed",
      detail: "Request failed.",
    });
  });
});
