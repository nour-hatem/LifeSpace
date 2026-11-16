export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;

  constructor(status: number, code: string, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

type ProblemBody = {
  code?: unknown;
  detail?: unknown;
};

const GENERIC_DETAIL = "Request failed.";

async function errorFromResponse(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/problem+json")) {
    return new ApiError(response.status, "failed", GENERIC_DETAIL);
  }

  try {
    const body = (await response.json()) as ProblemBody;
    const code = typeof body.code === "string" ? body.code : "failed";
    const detail = typeof body.detail === "string" ? body.detail : GENERIC_DETAIL;
    return new ApiError(response.status, code, detail);
  } catch {
    return new ApiError(response.status, "failed", GENERIC_DETAIL);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  return (await response.json()) as T;
}
