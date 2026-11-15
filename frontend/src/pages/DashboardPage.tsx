import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Alert, api, Vehicle } from "../api";

export default function DashboardPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    Promise.all([api.listVehicles(), api.listAlerts(true)]).then(([v, a]) => {
      setVehicles(v);
      setAlerts(a);
    });
  }, []);

  return (
    <>
      <h2>Dashboard</h2>
      <div className="grid-2">
        <div className="card">
          <h3>Registered vehicles</h3>
          <p style={{ fontSize: "2rem", margin: 0 }}>{vehicles.length}</p>
          <Link to="/vehicles">Manage vehicles →</Link>
        </div>
        <div className="card">
          <h3>Unread alerts</h3>
          <p style={{ fontSize: "2rem", margin: 0 }}>{alerts.length}</p>
          <Link to="/alerts">View alerts →</Link>
        </div>
      </div>
      <div className="card">
        <h3>Quick actions</h3>
        <p>
          <Link to="/scan">Scan a plate</Link> · <Link to="/logs">Review access logs</Link>
        </p>
      </div>
    </>
  );
}
