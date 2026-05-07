/**
 * API client with automatic token refresh.
 *
 * Token strategy
 * ──────────────
 * • Access token  — stored in memory (module-level variable) AND localStorage
 *                   as a fallback for page reloads.  Sent as Bearer header.
 * • Refresh token — HttpOnly cookie managed entirely by the browser.
 *                   The frontend never reads or writes it directly.
 *
 * Refresh flow
 * ────────────
 * 1. Any request returns 401 with detail "token_expired"
 * 2. apiFetch calls POST /auth/refresh (cookie is sent automatically)
 * 3. On success: store the new access token, retry the original request once
 * 4. On failure: clear local token, redirect to /login
 *
 * A single in-flight refresh promise is shared across concurrent requests so
 * we never fire multiple simultaneous refresh calls.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UploadResponse {
  resume_id: string;
  message: string;
}

export interface OptimizeResponse {
  optimized_cv: string;
  resume_id: string;
}

export interface OptimizationHistory {
  id: string;
  job_description: string;
  optimized_content: string;
  created_at: string;
}

export interface Resume {
  id: string;
  filename: string;
  raw_text: string;
  created_at: string;
  optimizations: OptimizationHistory[];
}

// ─── In-memory token store ────────────────────────────────────────────────────
// Keeping the token in a module variable means it survives React re-renders
// without triggering state updates, and is never exposed to third-party scripts
// via localStorage (though we still persist to localStorage for page-reload recovery).

let _accessToken: string | null = null;

export function getToken(): string | null {
  if (_accessToken) return _accessToken;
  if (typeof window === "undefined") return null;
  // Recover from page reload
  const stored = localStorage.getItem("access_token");
  if (stored) _accessToken = stored;
  return _accessToken;
}

export function setToken(token: string): void {
  _accessToken = token;
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", token);
  }
}

export function removeToken(): void {
  _accessToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

// ─── Refresh token logic ──────────────────────────────────────────────────────

// Shared promise so concurrent requests don't each fire a refresh
let _refreshPromise: Promise<string | null> | null = null;

/**
 * Call POST /auth/refresh.  The HttpOnly cookie is sent automatically by the
 * browser.  Returns the new access token on success, null on failure.
 */
async function callRefreshEndpoint(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include", // send the HttpOnly cookie
    });

    if (!res.ok) return null;

    const data: TokenResponse = await res.json();
    setToken(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  // Deduplicate concurrent refresh calls
  if (!_refreshPromise) {
    _refreshPromise = callRefreshEndpoint().finally(() => {
      _refreshPromise = null;
    });
  }
  return _refreshPromise;
}

// ─── Base fetch wrapper ───────────────────────────────────────────────────────

interface ApiFetchOptions extends RequestInit {
  _isRetry?: boolean; // internal flag to prevent infinite retry loops
}

async function apiFetch<T>(
  endpoint: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { _isRetry = false, ...fetchOptions } = options;

  const token = getToken();
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(fetchOptions.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
    credentials: "include", // always include cookies (needed for refresh)
  });

  // ── Token expired: attempt refresh then retry once ──────────────────────
  if (res.status === 401 && !_isRetry) {
    let detail = "";
    try {
      const body = await res.clone().json();
      detail = body?.detail ?? "";
    } catch {
      // ignore parse errors
    }

    // Only auto-refresh on "token_expired"; other 401s (bad creds etc.) fall through
    if (detail === "token_expired") {
      const newToken = await refreshAccessToken();

      if (newToken) {
        // Retry the original request with the new token
        return apiFetch<T>(endpoint, { ...options, _isRetry: true });
      } else {
        // Refresh failed — clear state and redirect to login
        removeToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        throw new Error("Session expired. Please log in again.");
      }
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export async function loginUser(
  email: string,
  password: string
): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login/access-token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include", // receive the refresh token cookie
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Login failed");
  }

  const data: TokenResponse = await res.json();
  setToken(data.access_token);
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include", // send cookie so backend can revoke it
    });
  } catch {
    // Best-effort — always clear local state regardless
  } finally {
    removeToken();
  }
}

export async function registerUser(
  email: string,
  password: string,
  full_name?: string
): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name }),
  });
}

export async function forgotPassword(email: string): Promise<{ msg: string }> {
  return apiFetch<{ msg: string }>(`/auth/password-recovery/${email}`, {
    method: "POST",
  });
}

export async function resetPassword(
  token: string,
  new_password: string
): Promise<{ msg: string }> {
  const params = new URLSearchParams({ token, new_password });
  return apiFetch<{ msg: string }>(`/auth/reset-password/?${params.toString()}`, {
    method: "POST",
  });
}

// ─── User API ─────────────────────────────────────────────────────────────────

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/users/me");
}

export async function updateProfile(data: {
  full_name?: string;
  email?: string;
}): Promise<User> {
  return apiFetch<User>("/users/me", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ─── Resume / Optimizer API ───────────────────────────────────────────────────

export async function uploadResume(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<UploadResponse>("/optimize/upload", {
    method: "POST",
    body: formData,
  });
}

export async function optimizeResume(
  resume_id: string,
  job_description: string
): Promise<OptimizeResponse> {
  return apiFetch<OptimizeResponse>("/optimize/optimize", {
    method: "POST",
    body: JSON.stringify({ resume_id, job_description }),
  });
}

export async function optimizeSnippet(
  resume_id: string,
  job_description: string,
  snippet: string,
  context?: string,
  instruction?: string
): Promise<OptimizeResponse> {
  return apiFetch<OptimizeResponse>("/optimize/snippet", {
    method: "POST",
    body: JSON.stringify({ resume_id, job_description, snippet, context, instruction }),
  });
}

export async function getHistory(): Promise<Resume[]> {
  return apiFetch<Resume[]>("/optimize/history");
}

export async function getResumeDetails(resumeId: string): Promise<Resume> {
  return apiFetch<Resume>(`/optimize/resume/${resumeId}`);
}

export async function getResumePreview(
  resumeId: string,
  optimizationId?: string,
  templateId: string = "modern-1-blue"
): Promise<{ html: string }> {
  const params = new URLSearchParams();
  if (optimizationId) params.append("optimization_id", optimizationId);
  if (templateId) params.append("template_id", templateId);
  return apiFetch<{ html: string }>(
    `/optimize/resume/${resumeId}/preview?${params.toString()}`
  );
}

export async function downloadResumePdf(
  resumeId: string,
  optimizationId?: string,
  templateId: string = "modern-1-blue",
  format: string = "pdf"
) {
  const token = getToken();
  const params = new URLSearchParams();
  if (optimizationId) params.append("optimization_id", optimizationId);
  if (templateId) params.append("template_id", templateId);
  if (format) params.append("format", format);

  const res = await fetch(
    `${API_BASE}/optimize/resume/${resumeId}/download?${params.toString()}`,
    {
      headers: { Authorization: `Bearer ${token}` },
      credentials: "include",
    }
  );

  if (!res.ok) throw new Error("Failed to download file");

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const ext = format.toLowerCase() === "docx" ? "docx" : "pdf";
  a.download = `Optimized_Resume_${resumeId.slice(0, 8)}.${ext}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
