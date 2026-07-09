import type { ApiResponse, Meta } from "./types";

export const API_BASE: string = import.meta.env.VITE_API_BASE || "/api";

export class ApiRequestError extends Error {
  code: string;
  details: unknown;
  status: number;

  constructor(message: string, code: string, details: unknown, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export interface Unwrapped<T> {
  data: T;
  meta?: Meta;
}

async function parseResponse<T>(res: Response): Promise<Unwrapped<T>> {
  let body: ApiResponse<T> | null = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text) as ApiResponse<T>;
    } catch {
      throw new ApiRequestError(
        `Invalid JSON response (HTTP ${res.status})`,
        "invalid_json",
        text.slice(0, 500),
        res.status
      );
    }
  }

  if (!body) {
    if (!res.ok) {
      throw new ApiRequestError(
        `Request failed with status ${res.status}`,
        "http_error",
        null,
        res.status
      );
    }
    return { data: undefined as unknown as T };
  }

  if (body.success === false) {
    throw new ApiRequestError(
      body.error?.message || "Request failed",
      body.error?.code || "error",
      body.error?.details,
      res.status
    );
  }

  if (!res.ok) {
    throw new ApiRequestError(
      `Request failed with status ${res.status}`,
      "http_error",
      body,
      res.status
    );
  }

  return { data: body.data, meta: body.meta };
}

function buildUrl(path: string, params?: Record<string, unknown>): string {
  const base = path.startsWith("http")
    ? path
    : `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  if (!params) return base;
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    qs.append(key, String(value));
  }
  const query = qs.toString();
  return query ? `${base}?${query}` : base;
}

export async function get<T>(
  path: string,
  params?: Record<string, unknown>
): Promise<Unwrapped<T>> {
  const res = await fetch(buildUrl(path, params), {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  });
  return parseResponse<T>(res);
}

export async function post<T>(
  path: string,
  body?: unknown
): Promise<Unwrapped<T>> {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parseResponse<T>(res);
}

export async function postForm<T>(
  path: string,
  form: FormData
): Promise<Unwrapped<T>> {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: { Accept: "application/json" },
    credentials: "same-origin",
    body: form,
  });
  return parseResponse<T>(res);
}

export const api = { get, post, postForm, API_BASE };
