import { useState } from "react";
import { api } from "../api";

export default function ReportsPage() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function download(kind: "access" | "security") {
    setError("");
    setBusy(kind);
    try {
      await api.downloadReport(kind);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <h2>Reports</h2>
      <div className="card">
        <p>PDF exports for security officers and audit records.</p>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button type="button" disabled={busy !== null} onClick={() => download("access")}>
            {busy === "access" ? "Preparing…" : "Download access logs (PDF)"}
          </button>
          <button type="button" className="secondary" disabled={busy !== null} onClick={() => download("security")}>
            {busy === "security" ? "Preparing…" : "Download security summary (PDF)"}
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </div>
    </>
  );
}
