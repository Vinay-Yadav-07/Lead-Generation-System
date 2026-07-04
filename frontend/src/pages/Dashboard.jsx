import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getStats, discoverCompanies, discoverWebsites, scoreCompanies, generateLeads, verifyAll, sendApproved } from '../api'

const STAT_CARDS = [
  { key: 'total_leads', label: 'Total Leads', color: 'from-blue-600/20 to-blue-900/10', border: 'border-blue-700/30', icon: '👥' },
  { key: 'verified_leads', label: 'Verified Leads', color: 'from-emerald-600/20 to-emerald-900/10', border: 'border-emerald-700/30', icon: '✅' },
  { key: 'high_confidence', label: 'High Confidence', color: 'from-amber-600/20 to-amber-900/10', border: 'border-amber-700/30', icon: '⭐' },
  { key: 'approved_for_outreach', label: 'Approved for Outreach', color: 'from-brand-600/20 to-brand-900/10', border: 'border-brand-700/30', icon: '🚀' },
]

const PIPELINE_ACTIONS = [
  { id: 'discover', label: 'Discover Companies', icon: '🏢', fn: discoverCompanies, desc: 'Find companies matching ICP' },
  { id: 'review', label: 'Review Companies', icon: '👁️', link: '/companies', desc: 'Inspect discovered company list' },
  { id: 'websites', label: 'Discover Websites', icon: '🌐', fn: discoverWebsites, desc: 'Find company websites' },
  { id: 'generate', label: 'Generate Leads', icon: '⚡', fn: generateLeads, desc: 'Build enriched lead profiles' },
  { id: 'verify', label: 'Verify Leads', icon: '✔️', fn: verifyAll, desc: 'Verify email, phone, role' },
  { id: 'score', label: 'Score Leads', icon: '📈', fn: scoreCompanies, desc: 'Recalculate lead scoring' },
  { id: 'campaign', label: 'Outreach', icon: '📨', fn: sendApproved, desc: 'Send outreach to approved leads' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(null)
  const [log, setLog] = useState([])

  const fetchStats = async () => {
    try {
      const { data } = await getStats()
      setStats(data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    fetchStats()
    const t = setInterval(fetchStats, 15000)
    return () => clearInterval(t)
  }, [])

  const runAction = async (action) => {
    if (running) return
    if (action.link) {
      navigate(action.link)
      return
    }
    setRunning(action.id)
    const start = Date.now()
    addLog(`⏳ ${action.label} started...`)
    try {
      const { data } = await action.fn()
      const elapsed = ((Date.now() - start) / 1000).toFixed(1)
      const msg = data?.message || 'Done'
      const detail = data?.created !== undefined
        ? ` Created: ${data.created}, Updated: ${data.updated}, Skipped: ${data.skipped}`
        : data?.processed !== undefined ? ` Processed: ${data.processed}` : ''
      addLog(`✅ ${action.label} — ${msg}${detail} (${elapsed}s)`)
      fetchStats()
    } catch (err) {
      addLog(`❌ ${action.label} failed: ${err?.response?.data?.detail || err.message}`)
    }
    setRunning(null)
  }

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString()
    setLog(prev => [`[${time}] ${msg}`, ...prev].slice(0, 50))
  }

  const overview = stats?.overview || {}
  const leads = stats?.leads || {}
  const companies = stats?.companies || {}
  const outreach = stats?.outreach || {}

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time pipeline metrics and controls</p>
        </div>
        <Link to="/leads" className="btn-secondary text-xs">
          View All Leads →
        </Link>
      </div>

      {/* 4 Required Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map(({ key, label, color, border, icon }) => (
          <div key={key} className={`stat-card bg-gradient-to-br ${color} border ${border}`}>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">{label}</span>
              <span className="text-xl">{icon}</span>
            </div>
            <div className="text-3xl font-bold text-white">
              {loading ? (
                <div className="h-8 w-16 bg-slate-700/50 animate-pulse rounded" />
              ) : (
                overview[key] ?? 0
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Two-column: Pipeline Actions + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Controls */}
        <div className="lg:col-span-2 card p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <span>⚡</span> Pipeline Controls
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {PIPELINE_ACTIONS.map((action) => (
              <button
                key={action.id}
                onClick={() => runAction(action)}
                disabled={!!running}
                className={`
                  flex flex-col items-start gap-2 p-4 rounded-xl border transition-all duration-200 text-left
                  ${running === action.id
                    ? 'bg-brand-900/40 border-brand-600/50 text-brand-300'
                    : 'bg-surface-100 border-slate-700/40 hover:border-brand-700/50 hover:bg-surface-200 text-slate-300'
                  }
                  ${running && running !== action.id ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-lg">{action.icon}</span>
                  {running === action.id && (
                    <div className="w-3 h-3 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
                  )}
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{action.label}</div>
                  <div className="text-xs text-slate-500">{action.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <span>📊</span> Quick Stats
          </h2>
          <div className="space-y-3">
            {[
              { label: 'Companies Found', value: companies.total ?? 0 },
              { label: 'With Website', value: companies.with_website ?? 0 },
              { label: 'Leads w/ Email', value: leads.with_email ?? 0 },
              { label: 'Leads w/ Phone', value: leads.with_phone ?? 0 },
              { label: 'Email Verified', value: leads.email_verified ?? 0 },
              { label: 'Role Verified', value: leads.role_verified ?? 0 },
              { label: 'Emails Sent', value: outreach.sent ?? 0 },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-xs text-slate-400">{label}</span>
                <span className="text-sm font-semibold text-white">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Confidence Breakdown + Activity Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Confidence Breakdown</h2>
          {leads.by_confidence ? (
            <div className="space-y-3">
              {Object.entries(leads.by_confidence).map(([level, count]) => {
                const pct = leads.total > 0 ? Math.round((count / leads.total) * 100) : 0
                const color = level === 'HIGH' ? 'bg-emerald-500' : level === 'MEDIUM' ? 'bg-amber-500' : 'bg-red-500'
                return (
                  <div key={level}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">{level}</span>
                      <span className="text-white font-medium">{count} ({pct}%)</span>
                    </div>
                    <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-slate-500 text-sm">No data yet</p>
          )}
        </div>

        <div className="card p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Activity Log</h2>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {log.length === 0 ? (
              <p className="text-slate-500 text-xs">No activity yet. Run a pipeline action.</p>
            ) : (
              log.map((entry, i) => (
                <p key={i} className="text-xs text-slate-400 font-mono leading-relaxed">{entry}</p>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
