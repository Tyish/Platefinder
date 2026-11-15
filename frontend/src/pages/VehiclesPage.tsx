import { FormEvent, useEffect, useState } from "react";
import { api, Vehicle } from "../api";

export default function VehiclesPage() {
  const [items, setItems] = useState<Vehicle[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    plate_number: "",
    owner_name: "",
    owner_phone: "",
    make_model: "",
    expiry_date: "",
  });

  function load(search?: string) {
    api.listVehicles(search).then(setItems).catch((e) => setError(String(e.message)));
  }

  useEffect(() => {
    load();
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await api.createVehicle({
        plate_number: form.plate_number,
        owner_name: form.owner_name,
        owner_phone: form.owner_phone || null,
        make_model: form.make_model || null,
        expiry_date: form.expiry_date ? new Date(form.expiry_date).toISOString() : null,
      });
      setForm({ plate_number: "", owner_name: "", owner_phone: "", make_model: "", expiry_date: "" });
      setMessage("Vehicle registered.");
      load(q || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <>
      <h2>Vehicles</h2>
      <div className="grid-2">
        <div className="card">
          <h3>Register vehicle</h3>
          <form onSubmit={submit}>
            <label>Plate number</label>
            <input
              value={form.plate_number}
              onChange={(e) => setForm({ ...form, plate_number: e.target.value })}
              placeholder="KAA123A"
              required
            />
            <label>Owner name</label>
            <input
              value={form.owner_name}
              onChange={(e) => setForm({ ...form, owner_name: e.target.value })}
              required
            />
            <label>Phone</label>
            <input value={form.owner_phone} onChange={(e) => setForm({ ...form, owner_phone: e.target.value })} />
            <label>Make / model</label>
            <input value={form.make_model} onChange={(e) => setForm({ ...form, make_model: e.target.value })} />
            <label>License expiry</label>
            <input
              type="date"
              value={form.expiry_date}
              onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
            />
            <button type="submit">Save</button>
          </form>
          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="success">{message}</p> : null}
        </div>
        <div className="card">
          <h3>Search</h3>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Plate…" />
          <button type="button" onClick={() => load(q || undefined)}>
            Search
          </button>
          <table>
            <thead>
              <tr>
                <th>Plate</th>
                <th>Owner</th>
                <th>Status</th>
                <th>Expiry</th>
              </tr>
            </thead>
            <tbody>
              {items.map((v) => (
                <tr key={v.id}>
                  <td>{v.plate_number}</td>
                  <td>{v.owner_name}</td>
                  <td>{v.status}</td>
                  <td>{v.expiry_date ? new Date(v.expiry_date).toLocaleDateString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
