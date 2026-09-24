import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './App.css'
import { OverlayScrollbar } from './OverlayScrollbar.tsx'

const rawApi = import.meta.env.VITE_API_URL
const API_URL =
  rawApi === undefined || rawApi === null
    ? 'http://127.0.0.1:8000'
    : String(rawApi).replace(/\/$/, '')
const CHART_COLORS = ['#245ea8', '#3d7cc9', '#5f92d4', '#8bb0df', '#6a8fbf', '#9bb4d4']
const SOURCE_OPTIONS = ['', 'firewall', 'network', 'api', 'crowdstrike', 'aws', 'm365', 'ad']

type TabId = 'overview' | 'logs' | 'alerts' | 'ingest'
type Bucket = { key: string | number; count: number }

type DashboardData = {
  total_logs: number
  by_severity: Bucket[]
  by_event_type: Bucket[]
  top_ip: Bucket[]
  top_user: Bucket[]
  timeline: Bucket[]
}

type Filters = {
  tenant: string
  source: string
  timeFrom: string
  timeTo: string
}

type SessionUser = {
  username: string
  role: string
  tenant: string | null
}

type LogRow = {
  id: string
  '@timestamp'?: string
  tenant?: string
  source?: string
  severity?: number
  event_type?: string
  user?: string
  src_ip?: string
  host?: string
  action?: string
  raw?: unknown
  [key: string]: unknown
}

type AlertRow = {
  id: string
  timestamp?: string
  rule?: string
  count?: number
  severity?: number
  tenant?: string
  event_type?: string
  user?: string
  src_ip?: string
}

function severityClass(level: number | string | undefined) {
  const n = Number(level)
  if (n >= 5) return 'high'
  if (n >= 3) return 'mid'
  return ''
}

function shortTime(value: string | number) {
  const text = String(value)
  if (text.includes('T')) return text.slice(5, 16).replace('T', ' ')
  return text
}

function buildParams(filters: Filters, extra?: Record<string, string>) {
  const params = new URLSearchParams()
  if (filters.tenant.trim()) params.set('tenant', filters.tenant.trim())
  if (filters.source.trim()) params.set('source', filters.source.trim())
  if (filters.timeFrom.trim()) params.set('from', filters.timeFrom.trim())
  if (filters.timeTo.trim()) params.set('to', filters.timeTo.trim())
  if (extra) {
    for (const [k, v] of Object.entries(extra)) params.set(k, v)
  }
  return params
}

function toChartRows(items: Bucket[], limit = 6) {
  return items.slice(0, limit).map((item) => ({
    name: String(item.key),
    count: item.count,
  }))
}

type TooltipPayload = { value?: number | string; name?: string | number }

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string | number
}) {
  if (!active || !payload?.length) return null
  const row = payload[0]
  const title = label ?? row.name ?? ''
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{title}</div>
      <strong>{row.value}</strong>
    </div>
  )
}

function App() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [session, setSession] = useState<SessionUser | null>(() => {
    const raw = localStorage.getItem('session')
    return raw ? (JSON.parse(raw) as SessionUser) : null
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<TabId>('overview')

  const [logs, setLogs] = useState<LogRow[]>([])
  const [total, setTotal] = useState(0)
  const [logsLoading, setLogsLoading] = useState(false)
  const [selectedLog, setSelectedLog] = useState<LogRow | null>(null)
  const mainRef = useRef<HTMLElement>(null)

  const [filters, setFilters] = useState<Filters>({
    tenant: '',
    source: '',
    timeFrom: '',
    timeTo: '',
  })

  const [alerts, setAlerts] = useState<AlertRow[]>([])
  const [alertsTotal, setAlertsTotal] = useState(0)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)

  const [ingestJson, setIngestJson] = useState(
    '{\n  "tenant": "demoA",\n  "source": "api",\n  "event_type": "app_login_failed",\n  "user": "alice",\n  "ip": "203.0.113.7",\n  "reason": "wrong_password"\n}',
  )
  const [ingestBusy, setIngestBusy] = useState(false)
  const [ingestMsg, setIngestMsg] = useState('')
  const [lastRefresh, setLastRefresh] = useState<string>('')

  const isViewer = session?.role === 'viewer'
  const isAdmin = session?.role === 'admin'

  const timelineData = useMemo(
    () =>
      (dashboard?.timeline ?? [])
        .filter((t) => t.count > 0)
        .slice(-18)
        .map((t) => ({ name: shortTime(t.key), count: t.count })),
    [dashboard],
  )

  const topIpData = useMemo(() => toChartRows(dashboard?.top_ip ?? []), [dashboard])
  const topUserData = useMemo(() => toChartRows(dashboard?.top_user ?? []), [dashboard])
  const eventTypeData = useMemo(() => toChartRows(dashboard?.by_event_type ?? []), [dashboard])
  const severityData = useMemo(() => toChartRows(dashboard?.by_severity ?? [], 8), [dashboard])

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
        setError('Invalid username or password')
        setToken(null)
        setSession(null)
        return
      }

      const data = await res.json()
      const nextSession: SessionUser = {
        username: data.username,
        role: data.role,
        tenant: data.tenant ?? null,
      }

      setToken(data.access_token)
      setSession(nextSession)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('session', JSON.stringify(nextSession))
      setTab('overview')

      if (data.role === 'viewer' && data.tenant) {
        setFilters((f) => ({ ...f, tenant: data.tenant }))
      }
    } catch {
      setError('Cannot reach API. Check that the backend is running.')
      setToken(null)
      setSession(null)
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    setToken(null)
    setSession(null)
    localStorage.removeItem('token')
    localStorage.removeItem('session')
    setLogs([])
    setTotal(0)
    setFilters({ tenant: '', source: '', timeFrom: '', timeTo: '' })
    setDashboard(null)
    setAlerts([])
    setAlertsTotal(0)
    setSelectedLog(null)
    setIngestMsg('')
    setError('')
    setTab('overview')
  }

  function effectiveFilters(f: Filters): Filters {
    return {
      ...f,
      tenant: isViewer && session?.tenant ? session.tenant : f.tenant,
      timeFrom: f.timeFrom ? new Date(f.timeFrom).toISOString() : '',
      timeTo: f.timeTo ? new Date(f.timeTo).toISOString() : '',
    }
  }

  async function loadLogs(currentToken: string, f: Filters) {
    setLogsLoading(true)
    try {
      const params = buildParams(f, { size: '50' })
      const res = await fetch(`${API_URL}/api/logs?${params.toString()}`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      if (!res.ok) {
        setError('Failed to load logs')
        return
      }
      const data = await res.json()
      setLogs(data.logs ?? [])
      setTotal(data.total ?? 0)
    } catch {
      setError('Failed to call /api/logs')
    } finally {
      setLogsLoading(false)
    }
  }

  async function loadDashboard(currentToken: string, f: Filters) {
    try {
      const params = buildParams(f)
      const query = params.toString()
      const url = query ? `${API_URL}/api/dashboard?${query}` : `${API_URL}/api/dashboard`
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      if (!res.ok) {
        setError('Failed to load dashboard')
        return
      }
      const data = await res.json()
      setDashboard({
        total_logs: data.total_logs ?? 0,
        by_severity: data.by_severity ?? [],
        by_event_type: data.by_event_type ?? [],
        top_ip: data.top_ip ?? [],
        top_user: data.top_user ?? [],
        timeline: data.timeline ?? [],
      })
    } catch {
      setError('Failed to call /api/dashboard')
    }
  }

  async function loadAlerts(currentToken: string, f: Filters) {
    try {
      const params = new URLSearchParams()
      params.set('window_minutes', '5')
      params.set('min_count', '3')
      if (f.tenant.trim()) params.set('tenant', f.tenant.trim())
      const res = await fetch(`${API_URL}/api/alerts?${params.toString()}`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      if (!res.ok) {
        setError('Failed to load alerts')
        return
      }
      const data = await res.json()
      setAlerts(data.alerts ?? [])
      setAlertsTotal(data.total ?? 0)
    } catch {
      setError('Failed to call /api/alerts')
    }
  }

  function refreshAll(currentToken: string, f: Filters) {
    setError('')
    const ef = effectiveFilters(f)
    loadLogs(currentToken, ef)
    loadDashboard(currentToken, ef)
    loadAlerts(currentToken, ef)
    setLastRefresh(new Date().toLocaleTimeString())
  }

  useEffect(() => {
    if (!token) return
    const initial: Filters = {
      tenant: session?.role === 'viewer' && session.tenant ? session.tenant : '',
      source: '',
      timeFrom: '',
      timeTo: '',
    }
    setFilters(initial)
    refreshAll(token, initial)
  }, [token])

  useEffect(() => {
    if (!token) return
    const id = window.setInterval(() => {
      refreshAll(token, filters)
    }, 30000)
    return () => window.clearInterval(id)
  }, [token, filters, session])

  function applySearch() {
    if (!token) return
    refreshAll(token, filters)
  }

  function clearFilters() {
    if (!token) return
    const empty: Filters = {
      tenant: isViewer && session?.tenant ? session.tenant : '',
      source: '',
      timeFrom: '',
      timeTo: '',
    }
    setFilters(empty)
    refreshAll(token, empty)
  }

  async function submitJsonIngest() {
    if (!token || !isAdmin) return
    setIngestBusy(true)
    setIngestMsg('')
    setError('')
    try {
      const payload = JSON.parse(ingestJson)
      const res = await fetch(`${API_URL}/api/ingest`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setIngestMsg(`Ingest failed: ${res.status} ${JSON.stringify(data)}`)
        return
      }
      setIngestMsg(`Accepted · source=${data.source} · id=${data.id}`)
      refreshAll(token, filters)
    } catch (err) {
      setIngestMsg(err instanceof Error ? err.message : 'Invalid JSON or network error')
    } finally {
      setIngestBusy(false)
    }
  }

  async function uploadBatchFiles(fileList: FileList | null) {
    if (!token || !isAdmin || !fileList?.length) return
    setIngestBusy(true)
    setIngestMsg('')
    setError('')
    try {
      const form = new FormData()
      Array.from(fileList).forEach((f) => form.append('files', f))
      const res = await fetch(`${API_URL}/api/ingest/batch`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setIngestMsg(`Batch failed: ${res.status} ${JSON.stringify(data)}`)
        return
      }
      setIngestMsg(`Batch done · accepted=${data.accepted} · failed=${data.failed}`)
      refreshAll(token, filters)
      setTab('logs')
    } catch {
      setIngestMsg('Batch upload failed (network)')
    } finally {
      setIngestBusy(false)
    }
  }

  if (token && session) {
    const uniqueSources = new Set(logs.map((l) => l.source).filter(Boolean)).size
    const highSeverity = (dashboard?.by_severity ?? [])
      .filter((b) => Number(b.key) >= 5)
      .reduce((sum, b) => sum + b.count, 0)

    const tabs: { id: TabId; label: string; adminOnly?: boolean }[] = [
      { id: 'overview', label: 'Overview' },
      { id: 'logs', label: 'Logs' },
      { id: 'alerts', label: 'Alerts' },
      { id: 'ingest', label: 'Ingest', adminOnly: true },
    ]

    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="topbar-left">
            <div className="brand-mark" aria-hidden="true" />
            <div>
              <h1>Log Management Console</h1>
              <p className="topbar-sub">Multi-source security log console</p>
            </div>
          </div>
          <div className="topbar-right">
            {lastRefresh && <span className="refresh-meta">Updated {lastRefresh}</span>}
            <div className="user-chip">
              <strong>{session.username}</strong>
              <span>
                {session.role}
                {session.tenant ? ` · ${session.tenant}` : ' · all tenants'}
              </span>
            </div>
            <button type="button" className="btn" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </header>

        <div className="app-body">
          <main ref={mainRef} className="app-main hide-scrollbar">
            <div className="app-main-inner">
          {isViewer && (
            <div className="viewer-note">
              Viewer access is limited to tenant <strong>{session.tenant}</strong>.
            </div>
          )}

          <nav className="tab-nav" aria-label="Main sections">
            {tabs
              .filter((t) => !t.adminOnly || isAdmin)
              .map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={`tab-btn ${tab === t.id ? 'active' : ''}`}
                  onClick={() => setTab(t.id)}
                >
                  {t.label}
                  {t.id === 'alerts' && alertsTotal > 0 ? (
                    <span className="tab-badge">{alertsTotal}</span>
                  ) : null}
                </button>
              ))}
          </nav>

          <div className={`toolbar ${isViewer ? 'toolbar-viewer' : ''}`}>
            {!isViewer && (
              <label className="toolbar-field">
                <span>Tenant</span>
                <input
                  placeholder="e.g. demoA"
                  value={filters.tenant}
                  onChange={(e) => setFilters({ ...filters, tenant: e.target.value })}
                />
              </label>
            )}
            <label className="toolbar-field">
              <span>Source</span>
              <select
                value={filters.source}
                onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              >
                {SOURCE_OPTIONS.map((s) => (
                  <option key={s || 'all'} value={s}>
                    {s || 'All sources'}
                  </option>
                ))}
              </select>
            </label>
            <label className="toolbar-field">
              <span>From</span>
              <input
                type="datetime-local"
                value={filters.timeFrom}
                onChange={(e) => setFilters({ ...filters, timeFrom: e.target.value })}
              />
            </label>
            <label className="toolbar-field">
              <span>To</span>
              <input
                type="datetime-local"
                value={filters.timeTo}
                onChange={(e) => setFilters({ ...filters, timeTo: e.target.value })}
              />
            </label>
            <div className="toolbar-actions">
              <button type="button" className="btn btn-primary" onClick={applySearch}>
                Apply
              </button>
              <button type="button" className="btn" onClick={clearFilters}>
                Reset
              </button>
            </div>
          </div>

          {error && (
            <div className="banner-error" role="alert">
              {error}
            </div>
          )}

          {tab === 'overview' && dashboard && (
            <>
              <section className="kpi-grid" aria-label="Key metrics">
                <div className="kpi-card">
                  <h2>Total events</h2>
                  <div>
                    <div className="kpi-value">{dashboard.total_logs.toLocaleString()}</div>
                    <p className="kpi-sub">Indexed in OpenSearch</p>
                  </div>
                </div>
                <div className="kpi-card">
                  <h2>Active alerts</h2>
                  <div>
                    <div className="kpi-value">{alertsTotal.toLocaleString()}</div>
                    <p className="kpi-sub">Login-fail rule (5 min)</p>
                  </div>
                </div>
                <div className="kpi-card">
                  <h2>High severity</h2>
                  <div>
                    <div className="kpi-value">{highSeverity.toLocaleString()}</div>
                    <p className="kpi-sub">Severity ≥ 5</p>
                  </div>
                </div>
                <div className="kpi-card">
                  <h2>Sources in view</h2>
                  <div>
                    <div className="kpi-value">{uniqueSources || '—'}</div>
                    <p className="kpi-sub">From recent log rows</p>
                  </div>
                </div>
              </section>

              <section className="chart-grid" aria-label="Primary charts">
                <div className="panel">
                  <div className="panel-header">
                    <h2>Event timeline</h2>
                    <span className="panel-meta">hourly</span>
                  </div>
                  {timelineData.length === 0 ? (
                    <div className="chart-empty">No timeline data</div>
                  ) : (
                    <div className="chart-box">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={timelineData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="timelineFill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#245ea8" stopOpacity={0.35} />
                              <stop offset="100%" stopColor="#245ea8" stopOpacity={0.02} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid stroke="#e4eaf1" vertical={false} />
                          <XAxis
                            dataKey="name"
                            tick={{ fill: '#6a7a8f', fontSize: 11 }}
                            axisLine={{ stroke: '#cfd8e3' }}
                            tickLine={false}
                            interval="preserveStartEnd"
                          />
                          <YAxis
                            allowDecimals={false}
                            tick={{ fill: '#6a7a8f', fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                            width={32}
                          />
                          <Tooltip content={<ChartTooltip />} />
                          <Area
                            type="monotone"
                            dataKey="count"
                            stroke="#245ea8"
                            strokeWidth={2}
                            fill="url(#timelineFill)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>

                <div className="panel">
                  <div className="panel-header">
                    <h2>Severity distribution</h2>
                    <span className="panel-meta">share</span>
                  </div>
                  {severityData.length === 0 ? (
                    <div className="chart-empty">No severity data</div>
                  ) : (
                    <>
                      <div className="chart-box">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={severityData}
                              dataKey="count"
                              nameKey="name"
                              innerRadius={52}
                              outerRadius={84}
                              paddingAngle={2}
                            >
                              {severityData.map((_, idx) => (
                                <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip content={<ChartTooltip />} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <ul className="chart-legend">
                        {severityData.map((row, idx) => (
                          <li key={row.name}>
                            <span
                              className="chart-legend-swatch"
                              style={{ background: CHART_COLORS[idx % CHART_COLORS.length] }}
                            />
                            <span>sev {row.name}</span>
                            <strong>{row.count}</strong>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </section>

              <section className="chart-grid-2" aria-label="Top rankings">
                <div className="panel">
                  <div className="panel-header">
                    <h2>Top IP</h2>
                    <span className="panel-meta">src_ip</span>
                  </div>
                  {topIpData.length === 0 ? (
                    <div className="chart-empty">No IP data</div>
                  ) : (
                    <div className="chart-box sm">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={topIpData}
                          layout="vertical"
                          margin={{ top: 4, right: 12, left: 8, bottom: 4 }}
                        >
                          <CartesianGrid stroke="#e4eaf1" horizontal={false} />
                          <XAxis type="number" allowDecimals={false} tick={{ fill: '#6a7a8f', fontSize: 11 }} />
                          <YAxis
                            type="category"
                            dataKey="name"
                            width={100}
                            tick={{ fill: '#3f4f63', fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="count" fill="#245ea8" radius={[0, 4, 4, 0]} barSize={14} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>

                <div className="panel">
                  <div className="panel-header">
                    <h2>Top user</h2>
                    <span className="panel-meta">user</span>
                  </div>
                  {topUserData.length === 0 ? (
                    <div className="chart-empty">No user data</div>
                  ) : (
                    <div className="chart-box sm">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={topUserData}
                          layout="vertical"
                          margin={{ top: 4, right: 12, left: 8, bottom: 4 }}
                        >
                          <CartesianGrid stroke="#e4eaf1" horizontal={false} />
                          <XAxis type="number" allowDecimals={false} tick={{ fill: '#6a7a8f', fontSize: 11 }} />
                          <YAxis
                            type="category"
                            dataKey="name"
                            width={110}
                            tick={{ fill: '#3f4f63', fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="count" fill="#3d7cc9" radius={[0, 4, 4, 0]} barSize={14} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </section>

              <section className="panel" aria-label="Event types">
                <div className="panel-header">
                  <h2>Event type</h2>
                  <span className="panel-meta">by count</span>
                </div>
                {eventTypeData.length === 0 ? (
                  <div className="chart-empty">No event type data</div>
                ) : (
                  <div className="chart-box sm">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={eventTypeData} margin={{ top: 8, right: 8, left: 0, bottom: 28 }}>
                        <CartesianGrid stroke="#e4eaf1" vertical={false} />
                        <XAxis
                          dataKey="name"
                          tick={{ fill: '#6a7a8f', fontSize: 11 }}
                          interval={0}
                          angle={-18}
                          textAnchor="end"
                          height={50}
                        />
                        <YAxis allowDecimals={false} tick={{ fill: '#6a7a8f', fontSize: 11 }} width={32} />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={28}>
                          {eventTypeData.map((_, idx) => (
                            <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </section>
            </>
          )}

          {tab === 'alerts' && (
            <section className="panel" aria-labelledby="alerts-heading">
              <div className="panel-header">
                <h2 id="alerts-heading">Security alerts</h2>
                <span className="panel-meta">{alertsTotal}</span>
              </div>
              <p className="panel-desc">
                Rule: repeated login failures from the same IP (≥ 3) within 5 minutes
              </p>
              {alerts.length === 0 ? (
                <div className="panel-empty">
                  No active alerts. Seed failed logins from one IP to verify the rule.
                </div>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Rule</th>
                        <th>Count</th>
                        <th>Severity</th>
                        <th>Tenant</th>
                        <th>Event</th>
                        <th>User</th>
                        <th>IP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {alerts.map((a) => (
                        <tr key={a.id}>
                          <td className="cell-mono">{a.timestamp}</td>
                          <td>{a.rule ?? 'login_failed_same_ip'}</td>
                          <td>
                            <span className="sev-pill high">{a.count ?? '-'}</span>
                          </td>
                          <td>
                            <span className={`sev-pill ${severityClass(a.severity)}`}>
                              {a.severity}
                            </span>
                          </td>
                          <td>{a.tenant}</td>
                          <td>{a.event_type}</td>
                          <td>{a.user}</td>
                          <td className="cell-mono">{a.src_ip}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {tab === 'logs' && (
            <section className="panel" aria-labelledby="logs-heading">
              <div className="panel-header">
                <h2 id="logs-heading">Recent logs</h2>
                <span className="panel-meta">{total}</span>
              </div>
              {logsLoading ? (
                <div className="panel-loading">Loading logs…</div>
              ) : logs.length === 0 ? (
                <div className="panel-empty">No logs match the current filters</div>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Tenant</th>
                        <th>Source</th>
                        <th>Severity</th>
                        <th>Event</th>
                        <th>User</th>
                        <th>IP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr
                          key={log.id}
                          className="row-clickable"
                          onClick={() => setSelectedLog(log)}
                        >
                          <td className="cell-mono">{log['@timestamp']}</td>
                          <td>{log.tenant}</td>
                          <td>
                            <span className="source-chip">{log.source}</span>
                          </td>
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
          )}

          {tab === 'ingest' && isAdmin && (
            <section className="ingest-grid" aria-label="Ingest tools">
              <div className="panel">
                <div className="panel-header">
                  <h2>Upload sample files</h2>
                  <span className="panel-meta">POST /api/ingest/batch</span>
                </div>
                <p className="panel-desc">
                  Select one or more JSON files from <code>sample/</code> (AWS, M365, AD,
                  CrowdStrike). The API normalizes each document before indexing.
                </p>
                <label className="file-drop">
                  <input
                    type="file"
                    accept=".json,application/json"
                    multiple
                    disabled={ingestBusy}
                    onChange={(e) => {
                      void uploadBatchFiles(e.target.files)
                      e.target.value = ''
                    }}
                  />
                  <strong>Choose JSON files</strong>
                  <span>or drop them here (browser file picker)</span>
                </label>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h2>Paste JSON</h2>
                  <span className="panel-meta">POST /api/ingest</span>
                </div>
                <p className="panel-desc">Single event — useful for quick alert tests.</p>
                <textarea
                  className="ingest-textarea"
                  rows={12}
                  value={ingestJson}
                  onChange={(e) => setIngestJson(e.target.value)}
                  spellCheck={false}
                />
                <div className="ingest-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={ingestBusy}
                    onClick={() => void submitJsonIngest()}
                  >
                    {ingestBusy ? 'Sending…' : 'Send event'}
                  </button>
                </div>
              </div>

              {ingestMsg && (
                <div className="banner-ok" role="status">
                  {ingestMsg}
                </div>
              )}
            </section>
          )}
            </div>
          </main>
          <OverlayScrollbar targetRef={mainRef} />
        </div>

        {selectedLog && (
          <div className="drawer-backdrop" onClick={() => setSelectedLog(null)} role="presentation">
            <aside
              className="drawer"
              role="dialog"
              aria-label="Log detail"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="drawer-header">
                <h2>Event detail</h2>
                <button type="button" className="btn" onClick={() => setSelectedLog(null)}>
                  Close
                </button>
              </div>
              <dl className="detail-grid">
                <div>
                  <dt>Time</dt>
                  <dd className="cell-mono">{selectedLog['@timestamp']}</dd>
                </div>
                <div>
                  <dt>Tenant</dt>
                  <dd>{selectedLog.tenant}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>{selectedLog.source}</dd>
                </div>
                <div>
                  <dt>Severity</dt>
                  <dd>
                    <span className={`sev-pill ${severityClass(selectedLog.severity)}`}>
                      {selectedLog.severity}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>Event</dt>
                  <dd>{selectedLog.event_type}</dd>
                </div>
                <div>
                  <dt>Action</dt>
                  <dd>{selectedLog.action ?? '—'}</dd>
                </div>
                <div>
                  <dt>User</dt>
                  <dd>{selectedLog.user ?? '—'}</dd>
                </div>
                <div>
                  <dt>Host</dt>
                  <dd>{selectedLog.host ?? '—'}</dd>
                </div>
                <div>
                  <dt>IP</dt>
                  <dd className="cell-mono">{selectedLog.src_ip ?? '—'}</dd>
                </div>
              </dl>
              <h3 className="drawer-sub">Raw document</h3>
              <pre className="raw-block">{JSON.stringify(selectedLog, null, 2)}</pre>
            </aside>
          </div>
        )}
      </div>
    )
  }

  return (
    <main className="login-page hide-scrollbar">
      <div className="login-panel">
        <div className="login-brand">
          <div className="brand-mark" aria-hidden="true" />
          <div>
            <h1>Log Management</h1>
            <p>Security operations console</p>
          </div>
        </div>
        <p className="login-lead">
          Sign in to review dashboards, alerts, and tenant-scoped investigations.
        </p>
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
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <p className="login-hint">
          Demo accounts
          <br />
          <code>admin / admin123</code> — all tenants
          <br />
          <code>viewer / viewer123</code> — demoA only
        </p>
      </div>
    </main>
  )
}

export default App
