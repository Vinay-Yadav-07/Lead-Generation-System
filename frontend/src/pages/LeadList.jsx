import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getLeads, updateLeadStatus } from '../api'

const CONFIDENCE_BADGE = {
  HIGH: 'badge-high',
  MEDIUM: 'badge-medium',
  LOW: 'badge-low',
}

const STATUS_BADGE = {
  'New': 'badge-new',
  'Approved for Outreach': 'badge-approved',
  'Contacted': 'badge-contacted',
  'Do Not Contact': 'badge-dnc',
  'Reviewed': 'badge bg-slate-700/40 text-slate-300 border border-slate-600/40',
  'Replied': 'badge bg-purple-900/30 text-purple-300 border border-purple-700/30',
}

const STATUSES = ['New', 'Reviewed', 'Approved for Outreach', 'Do Not Contact', 'Contacted', 'Replied']

export default function LeadList() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ industry: '', status: '', confidence: '', search: '' })
  const [statusUpdating, setStatusUpdating] = useState(null)

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
      const { data } = await getLeads(params)
      setLeads(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }, [filters])

  useEffect(() => {
    const t = setTimeout(fetchLeads, 300)
    return () => clearTimeout(t)
  }, [fetchLeads])

  const handleStatusChange = async (e, lead) => {
    const newStatus = e.target.value
    setStatusUpdating(lead.id)
    try {
      await updateLeadStatus(lead.id, newStatus)
      setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, status: newStatus } : l))
    } catch {}
    setStatusUpdating(null)
  }

  const setFilter = (key, val) => setFilters(prev => ({ ...prev, [key]: val }))

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Lead List</h1>
          <p className="text-sm text-slate-400 mt-1">{leads.length} lead{leads.length !== 1 ? 's' : ''} found</p>
        </div>
      </div>

      {/* Filters — 5 required: Industry, Country (search), Status, Confidence, Search */}
      <div className="card p-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
            <input
              id="lead-search"
              type="search"
              placeholder="Search name, company, email"
              className="input pl-8"
              value={filters.search}
              onChange={e => setFilter('search', e.target.value)}
            />
          </div>

          {/* Industry filter */}
          <input
            id="lead-filter-industry"
            type="text"
            placeholder="Industry"
            className="input"
            value={filters.industry}
            onChange={e => setFilter('industry', e.target.value)}
          />

          {/* Country / search filter */}
          <input
            id="lead-filter-country"
            type="text"
            placeholder="Country"
            className="input"
            value={filters.country || ''}
            onChange={e => setFilter('country', e.target.value)}
          />

          {/* Status filter */}
          <div className="relative">
            <select
              id="lead-filter-status"
              className="select"
              value={filters.status}
              onChange={e => setFilter('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* Confidence filter */}
          <div className="relative">
            <select
              id="lead-filter-confidence"
              className="select"
              value={filters.confidence}
              onChange={e => setFilter('confidence', e.target.value)}
            >
              <option value="">All Confidence</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Name</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Company</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Email</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Phone</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Industry</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Score</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-slate-700/30">
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-3 bg-slate-700/40 animate-pulse rounded" style={{ width: `${60 + Math.random() * 40}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : leads.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-12 text-slate-500">
                    <div className="text-4xl mb-2">👥</div>
                    <p>No leads found. Run the pipeline to generate leads.</p>
                  </td>
                </tr>
              ) : (
                leads.map(lead => (
                  <tr key={lead.id} className="table-row">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{lead.full_name || '—'}</div>
                      <div className="text-xs text-slate-500">{lead.job_title || ''}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-slate-200">{lead.company_name || '—'}</div>
                      {lead.company_website && (
                        <a href={lead.company_website} target="_blank" rel="noreferrer"
                          className="text-xs text-brand-400 hover:underline">
                          {lead.company_website.replace(/^https?:\/\//, '').substring(0, 30)}
                        </a>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-slate-300 font-mono text-xs">{lead.email || '—'}</div>
                      {lead.email_verified && (
                        <span className="text-xs text-emerald-400">✓ Verified</span>
                      )}
                      {lead.email_source && (
                        <span className="ml-1 text-xs text-slate-500">[{lead.email_source}]</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-slate-300 text-xs font-mono">{lead.phone || '—'}</div>
                      {lead.phone_verified && (
                        <span className="text-xs text-emerald-400">✓ {lead.line_type || 'Verified'}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{lead.industry || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{lead.confidence_score ?? '—'}</span>
                        {lead.confidence_level && (
                          <span className={CONFIDENCE_BADGE[lead.confidence_level] || 'badge bg-slate-700/40 text-slate-400'}>
                            {lead.confidence_level}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {statusUpdating === lead.id ? (
                        <div className="w-4 h-4 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
                      ) : (
                        <select
                          className="text-xs bg-surface-100 border border-slate-700/40 rounded-md px-2 py-1 text-slate-300 focus:outline-none"
                          value={lead.status || 'New'}
                          onChange={e => handleStatusChange(e, lead)}
                          onClick={e => e.stopPropagation()}
                        >
                          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/leads/${lead.id}`}
                        className="text-brand-400 hover:text-brand-300 text-xs font-medium hover:underline"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
