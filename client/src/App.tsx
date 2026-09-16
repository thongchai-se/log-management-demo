import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function severityClass(level: number | string) {
  const n = Number(level)
  if (n >= 5) return 'sev-5'
  if (n === 4) return 'sev-4'
  if (n === 3) return 'sev-3'
  if (n === 2) return 'sev-2'
  return 'sev-1'
}

function maxCount(items: { count: number }[]) {
  return Math.max(1, ...items.map((i) => i.count))
}

function App() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [logsLoading, setLogsLoading] = useState(false)
  const [tenantFilter, setTenantFilter] = useState('')

  const [alerts, setAlerts] = useState<any[]>([])
  const [alertsTotal, setAlertsTotal] = useState(0)

  const [dashboard, setDashboard] = useState<{
    total_logs: number
    by_severity: { key: number; count: number }[]
    by_event_type: { key: string; count: number }[]
  } | null>(null)

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (!res.ok) {
        setError('Login ไม่สำเร็จ (ตรวจ username และ password อีกครั้ง)')
        setToken(null)
        return
      }

      const data = await res.json()
      setToken(data.access_token)
      localStorage.setItem('token', data.access_token)
    } catch {
      setError('เรียก API ไม่สำเร็จ ตรวจสอบว่า backend ยังรันอยู่')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    setToken(null)
    localStorage.removeItem('token')
    setLogs([])
    setTotal(0)
    setTenantFilter('')
    setDashboard(null)
    setAlerts([])
    setAlertsTotal(0)
    setError('')
  }

  async function loadLogs(currentToken: string, tenant?: string) {
    setLogsLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()
      params.set('size', '20')

      if (tenant && tenant.trim() !== '') {
        params.set('tenant', tenant.trim())
      }

      const res = await fetch(`${API_URL}/api/logs?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      })

      if (!res.ok) {
        setError('โหลด logs ไม่สำเร็จ')
        return
      }

      const data = await res.json()
      setLogs(data.logs)
      setTotal(data.total)
    } catch {
      setError('เรียก /api/logs ไม่สำเร็จ')
    } finally {
      setLogsLoading(false)
    }
  }

  async function loadDashboard(currentToken: string, tenant?: string) {
    try {
      const params = new URLSearchParams()
      if (tenant && tenant.trim() !== '') {
        params.set('tenant', tenant.trim())
      }

      const query = params.toString()
      const url = query
        ? `${API_URL}/api/dashboard?${query}`
        : `${API_URL}/api/dashboard`

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      })

      if (!res.ok) {
        setError('โหลด dashboard ไม่สำเร็จ')
        return
      }

      const data = await res.json()
      setDashboard(data)
    } catch {
      setError('เรียก /api/dashboard ไม่สำเร็จ')
    }
  }

  async function loadAlerts(currentToken: string, tenant?: string) {
    try {
      const params = new URLSearchParams()
      params.set('min_severity', '3')

      if (tenant && tenant.trim() !== '') {
        params.set('tenant', tenant.trim())
      }

      const res = await fetch(`${API_URL}/api/alerts?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      })

      if (!res.ok) {
        setError('โหลด alerts ไม่สำเร็จ')
        return
      }

      const data = await res.json()
      setAlerts(data.alerts)
      setAlertsTotal(data.total)
    } catch {
      setError('เรียก /api/alerts ไม่สำเร็จ')
    }
  }

  function refreshAll(currentToken: string, tenant: string) {
    loadLogs(currentToken, tenant)
    loadDashboard(currentToken, tenant)
    loadAlerts(currentToken, tenant)
  }

  useEffect(() => {
    if (token) {
      refreshAll(token, '')
    }
  }, [token])

  if (token) {
    const sevMax = dashboard ? maxCount(dashboard.by_severity) : 1
    const eventMax = dashboard ? maxCount(dashboard.by_event_type) : 1

    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark" aria-hidden="true" />
            <div className="brand-text">
              <h1>Log Management</h1>
              <p>ค้นหา · สรุป · แจ้งเตือน</p>
            </div>
          </div>
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            Logout
          </button>
        </header>

        <main className="app-main">
          <div className="toolbar">
            <input
              placeholder="กรอง tenant เช่น DemoA"
              value={tenantFilter}
              onChange={(e) => setTenantFilter(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') refreshAll(token, tenantFilter)
              }}
              aria-label="กรอง tenant"
            />
            <div className="toolbar-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => refreshAll(token, tenantFilter)}
              >
                ค้นหา
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setTenantFilter('')
                  refreshAll(token, '')
                }}
              >
                ล้างกรอง
              </button>
            </div>
          </div>

          {error && <div className="banner-error" role="alert">{error}</div>}

          {dashboard && (
            <section className="stats-grid" aria-label="สรุปภาพรวม">
              <div className="stat-panel">
                <h2>Total logs</h2>
                <div className="stat-value">{dashboard.total_logs.toLocaleString()}</div>
                <p className="stat-sub">แสดงในตาราง {total.toLocaleString()} รายการล่าสุด</p>
              </div>

              <div className="stat-panel">
                <h2>By severity</h2>
                {dashboard.by_severity.length === 0 ? (
                  <p className="empty-inline">ยังไม่มีข้อมูล</p>
                ) : (
                  <div className="dist-list">
                    {dashboard.by_severity.map((item) => (
                      <div className="dist-row" key={item.key}>
                        <span className="label">sev {item.key}</span>
                        <div className="bar-track">
                          <div
                            className={`bar-fill ${severityClass(item.key)}`}
                            style={{ transform: `scaleX(${item.count / sevMax})` }}
                          />
                        </div>
                        <span className="count">{item.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="stat-panel">
                <h2>By event type</h2>
                {dashboard.by_event_type.length === 0 ? (
                  <p className="empty-inline">ยังไม่มีข้อมูล</p>
                ) : (
                  <div className="dist-list">
                    {dashboard.by_event_type.map((item) => (
                      <div className="dist-row" key={item.key}>
                        <span className="label" title={item.key}>
                          {item.key}
                        </span>
                        <div className="bar-track">
                          <div
                            className="bar-fill"
                            style={{ transform: `scaleX(${item.count / eventMax})` }}
                          />
                        </div>
                        <span className="count">{item.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="panel" aria-labelledby="alerts-heading">
            <div className="panel-header">
              <h2 id="alerts-heading">Alerts</h2>
              <span className={`badge ${alertsTotal > 0 ? 'badge-alert' : ''}`}>
                {alertsTotal}
              </span>
            </div>
            {alerts.length === 0 ? (
              <div className="panel-empty">ไม่มีรายการแจ้งเตือน (severity ≥ 3)</div>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Severity</th>
                      <th>Tenant</th>
                      <th>Event</th>
                      <th>User</th>
                      <th>IP</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((a) => (
                      <tr key={a.id}>
                        <td className="cell-mono">{a.timestamp}</td>
                        <td>
                          <span className={`sev-pill ${severityClass(a.severity)}`}>
                            {a.severity}
                          </span>
                        </td>
                        <td>{a.tenant}</td>
                        <td>{a.event_type}</td>
                        <td>{a.user}</td>
                        <td className="cell-mono">{a.src_ip}</td>
                        <td>{a.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel" aria-labelledby="logs-heading">
            <div className="panel-header">
              <h2 id="logs-heading">Recent logs</h2>
              <span className="badge">{total}</span>
            </div>
            {logsLoading ? (
              <div className="panel-loading">
                <span className="spinner" aria-hidden="true" />
                กำลังโหลด logs...
              </div>
            ) : logs.length === 0 ? (
              <div className="panel-empty">ยังไม่มี log ในช่วงนี้</div>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Tenant</th>
                      <th>Severity</th>
                      <th>Event</th>
                      <th>User</th>
                      <th>IP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td className="cell-mono">{log['@timestamp']}</td>
                        <td>{log.tenant}</td>
                        <td>
                          <span className={`sev-pill ${severityClass(log.severity)}`}>
                            {log.severity}
                          </span>
                        </td>
                        <td>{log.event_type}</td>
                        <td>{log.user}</td>
                        <td className="cell-mono">{log.src_ip}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </main>
      </div>
    )
  }

  return (
    <main className="login-page">
      <div className="login-panel">
        <h1>Log Management</h1>
        <p className="login-lead">เข้าสู่ระบบเพื่อดู dashboard, alerts และ logs</p>
        <form onSubmit={handleLogin}>
          <label className="field">
            <span>Username</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'กำลังเข้าสู่ระบบ...' : 'Login'}
          </button>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </main>
  )
}

export default App
