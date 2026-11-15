
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [rejected, setRejected] = useState([]);
  const [page, setPage] = useState("Overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [runMessage, setRunMessage] = useState("");

  // Fetch dashboard data from FastAPI
  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [statsRes, runsRes, customersRes, rejectedRes] =
        await Promise.all([
          fetch(`${API}/statistics`),
          fetch(`${API}/pipeline-runs`),
          fetch(`${API}/customers`),
          fetch(`${API}/rejected-events`),
        ]);

      if (![statsRes, runsRes, customersRes, rejectedRes].every(r => r.ok)) {
        throw new Error("Could not fetch dashboard data.");
      }

      const [statsData, runsData, customersData, rejectedData] =
        await Promise.all([
          statsRes.json(),
          runsRes.json(),
          customersRes.json(),
          rejectedRes.json(),
        ]);

      setStats(statsData);
      setRuns(runsData);
      setCustomers(customersData);
      setRejected(rejectedData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Trigger the Python CDC pipeline through FastAPI
  async function triggerPipeline() {
    setRunning(true);
    setRunMessage("");
    setError("");

    try {
      const response = await fetch(`${API}/run-pipeline`, {
        method: "POST",
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Pipeline execution failed");
      }

      setRunMessage(
        `Pipeline completed: ${result.status} | Run ID: ${result.run_id}`
      );

      // Refresh dashboard after execution
      await loadDashboard();

    } catch (err) {
      setRunMessage(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const navigation = [
    { name: "Overview", icon: "▦" },
    { name: "Pipeline Runs", icon: "◷" },
    { name: "Customers", icon: "♙" },
    { name: "Rejected Events", icon: "⚠" },
  ];

  function renderOverview() {
    return (
      <>
        <div className="stats-grid">
          <StatCard title="Total Customers" value={stats?.total_customers} icon="♙" color="blue" />
          <StatCard title="History Events" value={stats?.total_history_events} icon="▤" color="purple" />
          <StatCard title="Processed Events" value={stats?.total_processed_events} icon="✓" color="green" />
          <StatCard title="Rejected Events" value={stats?.total_rejected_events} icon="⚠" color="orange" />
        </div>

        <div className="content-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Recent Pipeline Runs</h2>
                <p>Latest execution activity</p>
              </div>
              <button className="text-button" onClick={() => setPage("Pipeline Runs")}>
                View all →
              </button>
            </div>
            <RunTable runs={runs.slice(0, 5)} />
          </section>

          <section className="panel summary-panel">
            <h2>System Summary</h2>
            <p className="muted">Current database overview</p>
            <SummaryRow label="Pipeline executions" value={stats?.total_pipeline_runs} />
            <SummaryRow label="Customer records" value={stats?.total_customers} />
            <SummaryRow label="Event history" value={stats?.total_history_events} />
            <SummaryRow label="Rejected records" value={stats?.total_rejected_events} />
            <div className="system-status">
              <span className="status-dot" /> API connected
            </div>
          </section>
        </div>
      </>
    );
  }

  function renderPage() {
    if (page === "Overview") return renderOverview();

    if (page === "Pipeline Runs") {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Pipeline Execution History</h2>
              <p>All recorded pipeline runs</p>
            </div>
          </div>
          <RunTable runs={runs} />
        </section>
      );
    }

    if (page === "Customers") {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Customer Records</h2>
              <p>Latest customer state from MySQL</p>
            </div>
            <span className="count-label">{customers.length} records</span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>City</th>
                  <th>Version</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr key={c.customer_id}>
                    <td>{c.customer_id}</td>
                    <td>{c.customer_name || "—"}</td>
                    <td>{c.email || "—"}</td>
                    <td>{c.city || "—"}</td>
                    <td>v{c.source_version}</td>
                    <td>
                      <Status value={c.is_deleted ? "DELETED" : "ACTIVE"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      );
    }

    return (
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Rejected Events</h2>
            <p>Events that failed validation or processing</p>
          </div>
          <span className="count-label">{rejected.length} records</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Customer ID</th>
                <th>Reason</th>
                <th>Run ID</th>
                <th>Rejected At</th>
              </tr>
            </thead>
            <tbody>
              {rejected.map((r) => (
                <tr key={r.rejection_id}>
                  <td>{r.event_id || "—"}</td>
                  <td>{r.customer_id || "—"}</td>
                  <td>{r.rejection_reason}</td>
                  <td>{r.run_id}</td>
                  <td>{formatDate(r.rejected_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">D</div>
          <div>
            <strong>DataPulse</strong>
            <span>CDC MONITOR</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav>
          {navigation.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${page === item.name ? "active" : ""}`}
              onClick={() => setPage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="online-indicator">
            <span /> Backend connected
          </div>
          <small>CDC Pipeline v1.0.0</small>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace / <strong>{page}</strong>
            </div>
            <h1>{page}</h1>
          </div>

          <div className="topbar-actions">
            <button
              className="run-button"
              onClick={triggerPipeline}
              disabled={running}
            >
              {running ? "Running pipeline..." : "▶ Run Pipeline"}
            </button>

            <button
              className="refresh-button"
              onClick={loadDashboard}
              disabled={loading || running}
            >
              ↻ <span>Refresh data</span>
            </button>
          </div>
        </header>

        {runMessage && (
          <div className="run-message">
            {runMessage}
          </div>
        )}

        {error && (
          <div className="error-banner">
            ⚠ {error} — Check that FastAPI is running.
          </div>
        )}

        {loading ? (
          <div className="loading">Loading dashboard data...</div>
        ) : (
          <div className="page-content">{renderPage()}</div>
        )}

        <footer>
          DataPulse CDC Monitor <span>•</span> Powered by FastAPI + MySQL
        </footer>
      </main>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value ?? "—"}</div>
      <div className="stat-caption">Live database metric</div>
    </div>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}

function Status({ value }) {
  return (
    <span
      className={`status-badge ${
        value === "SUCCESS" || value === "ACTIVE"
          ? "success"
          : value === "PARTIAL_SUCCESS"
          ? "warning"
          : "danger"
      }`}
    >
      {value}
    </span>
  );
}

function RunTable({ runs }) {
  if (!runs.length) return <p className="empty">No pipeline runs found.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Status</th>
            <th>Total</th>
            <th>Accepted</th>
            <th>Rejected</th>
            <th>Started</th>
          </tr>
        </thead>

        <tbody>
          {runs.map((r) => (
            <tr key={r.run_id}>
              <td className="run-id">{r.run_id}</td>
              <td><Status value={r.status} /></td>
              <td>{r.total_events}</td>
              <td>{r.accepted_events}</td>
              <td>{r.rejected_events}</td>
              <td>{formatDate(r.start_time)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export default App;
