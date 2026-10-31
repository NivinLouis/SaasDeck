import type { ValidationErrorResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  fields?: Record<string, string[]>;

  constructor(message: string, public readonly status: number, fields?: Record<string, string[]>) {
    super(message);
    this.name = "ApiError";
    this.fields = fields;
  }
}

type ApiOptions = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  token?: string;
};

async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { body, token, ...init } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return undefined as T;

  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = data as Partial<ValidationErrorResponse> & { detail?: string } | null;
    throw new ApiError(error?.message ?? error?.detail ?? "Something went wrong. Please try again.", response.status, error?.fields);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string, token?: string) => request<T>(path, { method: "GET", token }),
  post: <T>(path: string, body?: unknown, token?: string) => request<T>(path, { method: "POST", body, token }),
  patch: <T>(path: string, body: unknown, token: string) => request<T>(path, { method: "PATCH", body, token }),
};
