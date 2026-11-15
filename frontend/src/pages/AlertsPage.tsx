import { useEffect, useState } from "react";
import { Alert, api } from "../api";

function alertBadgeClass(type: string): string {
  if (type === "authorized") return "ok";
  if (type === "expiry_soon") return "warn";
  return "bad";
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [message, setMessage] = useState("");

  function refresh() {
    api.listAlerts().then(setAlerts);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function runExpiryCheck() {
    const created = await api.checkExpiry();
    setMessage(`Expiry check complete (${created.length} new alert(s)).`);
    refresh();
  }

  async function markRead(id: number) {
    await api.markAlertRead(id);
    refresh();
  }

  return (
    <>
      <h2>Alerts</h2>
      <div className="card">
        <button type="button" onClick={runExpiryCheck}>
          Run expiry check (14 days)
        </button>
        {message ? <p className="success">{message}</p> : null}
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>Plate</th>
              <th>Message</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString()}</td>
                <td>
                  <span className={`badge ${alertBadgeClass(a.alert_type)}`}>{a.alert_type}</span>
                </td>
                <td>{a.plate_number}</td>
                <td>{a.message}</td>
                <td>
                  {!a.is_read ? (
                    <button type="button" className="secondary" onClick={() => markRead(a.id)}>
                      Mark read
                    </button>
                  ) : (
                    "Read"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
