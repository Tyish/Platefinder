import { useEffect, useState } from "react";
import { AccessLog, api } from "../api";

export default function LogsPage() {
  const [logs, setLogs] = useState<AccessLog[]>([]);

  useEffect(() => {
    api.listLogs().then(setLogs);
  }, []);

  return (
    <>
      <h2>Access logs</h2>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Plate</th>
              <th>Direction</th>
              <th>Authorized</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.plate_number}</td>
                <td>{log.direction}</td>
                <td>
                  <span className={`badge ${log.authorized ? "ok" : "bad"}`}>
                    {log.authorized ? "Yes" : "No"}
                  </span>
                </td>
                <td>{log.confidence ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
