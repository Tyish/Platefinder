import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api, User } from "./api";
import AlertsPage from "./pages/AlertsPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import LogsPage from "./pages/LogsPage";
import ReportsPage from "./pages/ReportsPage";
import ScanPage from "./pages/ScanPage";
import VehiclesPage from "./pages/VehiclesPage";

function Shell({ user, onLogout }: { user: User; onLogout: () => void }) {
  const loc = useLocation();
  const nav = [
    { to: "/", label: "Dashboard" },
    { to: "/vehicles", label: "Vehicles" },
    { to: "/scan", label: "Scan plate" },
    { to: "/logs", label: "Access logs" },
    { to: "/alerts", label: "Alerts" },
    { to: "/reports", label: "Reports" },
  ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>AI License Plate Recognition</h1>
        <p style={{ fontSize: "0.8rem", opacity: 0.85, marginTop: "-1rem" }}>
          {user.full_name} ({user.role})
        </p>
        <nav>
          {nav.map((item) => (
            <Link key={item.to} to={item.to} className={loc.pathname === item.to ? "active" : ""}>
              {item.label}
            </Link>
          ))}
        </nav>
        <button type="button" className="secondary" style={{ marginTop: "1.5rem" }} onClick={onLogout}>
          Log out
        </button>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/vehicles" element={<VehiclesPage />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="login-page">
        <p>Loading…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={setUser} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Shell
      user={user}
      onLogout={() => {
        api.logout();
        setUser(null);
      }}
    />
  );
}
