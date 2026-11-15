const TOKEN_KEY = "lpr_token";

/** Render backend URL on Vercel. Locally leave unset to use Vite `/api` proxy. */
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type Vehicle = {
  id: number;
  plate_number: string;
  owner_name: string;
  owner_phone: string | null;
  make_model: string | null;
  expiry_date: string | null;
  status: string;
  created_at: string;
};

export type AccessLog = {
  id: number;
  plate_number: string;
  direction: string;
  authorized: boolean;
  confidence: string | null;
  notes: string | null;
  created_at: string;
};

export type Alert = {
  id: number;
  alert_type: string;
  plate_number: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type ScanResult = {
  plate_number: string | null;
  raw_text: string;
  confidence: number;
  authorized: boolean;
  vehicle: Vehicle | null;
  access_log: AccessLog | null;
  detected: boolean;
  alert_created: boolean;
  deduped: boolean;
  ocr_available: boolean;
};

export const api = {
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const data = await request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    setToken(data.access_token);
    return data;
  },
  logout: () => setToken(null),
  me: () => request<User>("/api/auth/me"),
  listVehicles: (q?: string) =>
    request<Vehicle[]>(`/api/vehicles${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  createVehicle: (payload: Record<string, unknown>) =>
    request<Vehicle>("/api/vehicles", { method: "POST", body: JSON.stringify(payload) }),
  deleteVehicle: (id: number) => request<void>(`/api/vehicles/${id}`, { method: "DELETE" }),
  listLogs: () => request<AccessLog[]>("/api/logs"),
  listAlerts: (unreadOnly = false) =>
    request<Alert[]>(`/api/alerts${unreadOnly ? "?unread_only=true" : ""}`),
  markAlertRead: (id: number) =>
    request<Alert>(`/api/alerts/${id}/read`, { method: "PATCH" }),
  checkExpiry: () => request<Alert[]>("/api/alerts/check-expiry", { method: "POST" }),
  scanManual: (plate_number: string, direction: string) =>
    request<ScanResult>("/api/scan/manual", {
      method: "POST",
      body: JSON.stringify({ plate_number, direction }),
    }),
  scanImage: (file: Blob | File, direction: string, source?: string) => {
    const fd = new FormData();
    const name = file instanceof File ? file.name : "capture.jpg";
    fd.append("file", file, name);
    const qs = new URLSearchParams({ direction });
    if (source) qs.set("source", source);
    return request<ScanResult>(`/api/scan/image?${qs.toString()}`, {
      method: "POST",
      body: fd,
    });
  },
  scanRtsp: (rtsp_url: string, direction: string) =>
    request<ScanResult>("/api/scan/rtsp", {
      method: "POST",
      body: JSON.stringify({ rtsp_url, direction }),
    }),
  downloadReport: async (kind: "access" | "security") => {
    const path = kind === "access" ? "/api/reports/access-logs.pdf" : "/api/reports/security-summary.pdf";
    const token = getToken();
    const res = await fetch(`${API_BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error("Could not download report");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = kind === "access" ? "access-logs.pdf" : "security-summary.pdf";
    a.click();
    URL.revokeObjectURL(url);
  },
};
