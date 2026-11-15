import { FormEvent, useEffect, useRef, useState } from "react";
import { Alert, api, ScanResult } from "../api";

const SCAN_INTERVAL_MS = 3000;
const ALERT_POLL_MS = 5000;

export default function ScanPage() {
  const [direction, setDirection] = useState("entry");
  const [manualPlate, setManualPlate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [rtspUrl, setRtspUrl] = useState("rtsp://");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [watching, setWatching] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [liveStatus, setLiveStatus] = useState("");
  const [unreadAlerts, setUnreadAlerts] = useState<Alert[]>([]);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const inFlightRef = useRef(false);
  const directionRef = useRef(direction);

  useEffect(() => {
    directionRef.current = direction;
  }, [direction]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  useEffect(() => {
    if (!watching) return;
    const id = window.setInterval(() => {
      void captureAndScan();
    }, SCAN_INTERVAL_MS);
    void captureAndScan();
    return () => window.clearInterval(id);
  }, [watching]);

  useEffect(() => {
    if (!watching) return;
    let cancelled = false;
    async function poll() {
      try {
        const alerts = await api.listAlerts(true);
        if (!cancelled) setUnreadAlerts(alerts);
      } catch {
        /* ignore poll errors while watching */
      }
    }
    void poll();
    const id = window.setInterval(poll, ALERT_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [watching]);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setWatching(false);
  }

  async function startWatching() {
    setCameraError("");
    setError("");
    setLiveStatus("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setWatching(true);
    } catch (err) {
      setCameraError(err instanceof Error ? err.message : "Could not open camera");
      stopCamera();
    }
  }

  async function captureAndScan() {
    if (inFlightRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return;

    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.85),
    );
    if (!blob) return;

    inFlightRef.current = true;
    setBusy(true);
    setError("");
    try {
      const scan = await api.scanImage(blob, directionRef.current, "live_webcam");
      setResult(scan);
      if (!scan.detected || !scan.plate_number) {
        setLiveStatus("No plate detected");
      } else if (scan.deduped) {
        setLiveStatus(
          scan.authorized
            ? `Same plate ${scan.plate_number} — recognized (skipped duplicate)`
            : `Same plate ${scan.plate_number} — not recognized (skipped duplicate)`,
        );
      } else if (scan.authorized) {
        setLiveStatus(`RECOGNIZED / AUTHORIZED — ${scan.plate_number}`);
      } else {
        setLiveStatus(`NOT RECOGNIZED / UNAUTHORIZED — ${scan.plate_number}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Live scan failed");
    } finally {
      inFlightRef.current = false;
      setBusy(false);
    }
  }

  async function runManual(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.scanManual(manualPlate, direction));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  async function runRtsp(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.scanRtsp(rtspUrl, direction));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  async function runImage(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.scanImage(file, direction));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  const latestUnread = unreadAlerts[0];

  return (
    <>
      <h2>Scan plate</h2>

      <div className="card live-camera-card">
        <h3>Live webcam</h3>
        <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: 0 }}>
          Auto-scans every {SCAN_INTERVAL_MS / 1000}s while watching. Alerts admin for recognized and
          unrecognized plates.
        </p>
        <label>Direction</label>
        <select value={direction} onChange={(e) => setDirection(e.target.value)} disabled={watching}>
          <option value="entry">Entry</option>
          <option value="exit">Exit</option>
        </select>
        <div className="live-camera-preview">
          <video ref={videoRef} playsInline muted className="live-video" />
          <canvas ref={canvasRef} className="live-canvas" />
        </div>
        <div className="live-camera-actions">
          {!watching ? (
            <button type="button" onClick={() => void startWatching()}>
              Start watching
            </button>
          ) : (
            <button type="button" className="danger" onClick={stopCamera}>
              Stop watching
            </button>
          )}
          {watching ? (
            <span className="badge ok">{busy ? "Scanning…" : "Watching"}</span>
          ) : null}
        </div>
        {cameraError ? <p className="error">{cameraError}</p> : null}
        {liveStatus ? (
          <div
            className={`live-status-banner ${
              liveStatus.startsWith("RECOGNIZED")
                ? "ok"
                : liveStatus.startsWith("NOT RECOGNIZED")
                  ? "bad"
                  : "neutral"
            }`}
          >
            {liveStatus}
          </div>
        ) : null}
        {watching ? (
          <div className="live-alert-strip">
            <strong>Unread alerts:</strong> {unreadAlerts.length}
            {latestUnread ? (
              <span>
                {" "}
                · Latest: <span className={`badge ${latestUnread.alert_type === "authorized" ? "ok" : "bad"}`}>
                  {latestUnread.alert_type}
                </span>{" "}
                {latestUnread.plate_number} — {latestUnread.message}
              </span>
            ) : (
              <span> · none</span>
            )}
          </div>
        ) : null}
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Manual (gate test)</h3>
          <form onSubmit={runManual}>
            <label>Direction</label>
            <select value={direction} onChange={(e) => setDirection(e.target.value)}>
              <option value="entry">Entry</option>
              <option value="exit">Exit</option>
            </select>
            <label>Plate number</label>
            <input value={manualPlate} onChange={(e) => setManualPlate(e.target.value)} required />
            <button type="submit" disabled={busy}>
              Record access
            </button>
          </form>
        </div>
        <div className="card">
          <h3>Image / camera upload</h3>
          <form onSubmit={runImage}>
            <label>Direction</label>
            <select value={direction} onChange={(e) => setDirection(e.target.value)}>
              <option value="entry">Entry</option>
              <option value="exit">Exit</option>
            </select>
            <label>Photo</label>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button type="submit" disabled={busy || !file}>
              Recognize &amp; log
            </button>
          </form>
          <p style={{ fontSize: "0.85rem", color: "#64748b" }}>
            Requires Tesseract on the server: <code>sudo apt install tesseract-ocr</code>
          </p>
        </div>
      </div>
      <div className="card">
        <h3>IP camera / RTSP stream</h3>
        <form onSubmit={runRtsp}>
          <label>Direction</label>
          <select value={direction} onChange={(e) => setDirection(e.target.value)}>
            <option value="entry">Entry</option>
            <option value="exit">Exit</option>
          </select>
          <label>Stream URL</label>
          <input
            value={rtspUrl}
            onChange={(e) => setRtspUrl(e.target.value)}
            placeholder="rtsp://user:pass@192.168.1.50:554/stream"
            required
          />
          <button type="submit" disabled={busy}>
            Capture frame &amp; recognize
          </button>
        </form>
        <p style={{ fontSize: "0.85rem", color: "#64748b" }}>
          Supports RTSP and many HTTP/MJPEG camera URLs supported by OpenCV.
        </p>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {result ? (
        <div className="card">
          <h3>Result</h3>
          {!result.detected || !result.plate_number ? (
            <p>No plate detected in this frame.</p>
          ) : (
            <>
              <p>
                Plate: <strong>{result.plate_number}</strong> · Confidence:{" "}
                {(result.confidence * 100).toFixed(0)}%
                {result.deduped ? " · deduped" : null}
                {result.alert_created ? " · alert created" : null}
              </p>
              <p>
                Access:{" "}
                <span className={`badge ${result.authorized ? "ok" : "bad"}`}>
                  {result.authorized ? "Authorized" : "Unauthorized / alert created"}
                </span>
              </p>
              {result.vehicle ? (
                <p>
                  Owner: {result.vehicle.owner_name} · Status: {result.vehicle.status}
                </p>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </>
  );
}
