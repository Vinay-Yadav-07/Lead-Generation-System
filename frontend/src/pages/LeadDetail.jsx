import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getLead, updateLeadStatus, getColdEmail, sendColdEmail } from '../api'

const STATUSES = ['New', 'Reviewed', 'Approved for Outreach', 'Do Not Contact', 'Contacted', 'Replied']

const BADGE = {
  HIGH: 'badge-high',
  MEDIUM: 'badge-medium',
  LOW: 'badge-low',
}

function InfoRow({ label, value, mono = false }) {
  if (!value && value !== 0) return null
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
      <span className={`text-sm text-slate-200 ${mono ? 'font-mono' : 'font-medium'}`}>{value}</span>
    </div>
  )
}

export default function LeadDetail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [emailDraft, setEmailDraft] = useState(null)
  const [loadingEmail, setLoadingEmail] = useState(false)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState('')

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data: res } = await getLead(id)
        setData(res)
        setSelectedStatus(res.lead?.status || 'New')
      } catch {}
      setLoading(false)
    }
    fetch()
  }, [id])

  const handleStatusUpdate = async () => {
    setStatusUpdating(true)
    try {
      await updateLeadStatus(id, selectedStatus)
      setData(prev => ({ ...prev, lead: { ...prev.lead, status: selectedStatus } }))
    } catch {}
    setStatusUpdating(false)
  }

  const fetchEmail = async () => {
    setLoadingEmail(true)
    try {
      const { data: draft } = await getColdEmail(id)
      setEmailDraft(draft)
    } catch {}
    setLoadingEmail(false)
  }

  const sendEmail = async () => {
    try {
      await sendColdEmail(id)
      alert('Email sent / simulated.')
      const { data: res } = await getLead(id)
      setData(res)
    } catch (e) {
      alert(e?.response?.data?.detail || 'Failed to send email.')
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-48 bg-slate-700/40 animate-pulse rounded" />
        <div className="card p-6">
          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="h-10 bg-slate-700/40 animate-pulse rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6">
        <p className="text-red-400">Lead not found.</p>
        <Link to="/leads" className="btn-secondary mt-4">← Back to Leads</Link>
      </div>
    )
  }

  const { lead, evidence = [], audit_trail = [] } = data

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      {/* Breadcrumb + Back */}
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link to="/leads" className="hover:text-white transition-colors">Leads</Link>
        <span>/</span>
        <span className="text-white">{lead.full_name || `Lead #${lead.id}`}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{lead.full_name || 'Unnamed Lead'}</h1>
          <p className="text-slate-400 mt-1">{lead.job_title || ''} {lead.company_name ? `@ ${lead.company_name}` : ''}</p>
        </div>
        <div className="flex items-center gap-2">
          {lead.confidence_level && (
            <span className={`badge text-sm px-3 py-1 ${BADGE[lead.confidence_level] || ''}`}>
              {lead.confidence_level}
            </span>
          )}
          <span className="text-2xl font-bold text-white">{lead.confidence_score ?? '—'}<span className="text-slate-500 text-sm">/10</span></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main info */}
        <div className="lg:col-span-2 space-y-5">
          {/* Contact Details */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><span>📧</span> Contact Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <InfoRow label="Email" value={lead.email} mono />
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-slate-500 uppercase tracking-wider">Email Status</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-200">{lead.email_status || '—'}</span>
                  {lead.email_verified && <span className="text-xs text-emerald-400 font-medium">✓ Verified</span>}
                </div>
                {lead.email_source && <span className="text-xs text-slate-500">[{lead.email_source}]</span>}
              </div>
              <InfoRow label="Phone" value={lead.phone} mono />
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-slate-500 uppercase tracking-wider">Phone Status</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-200">{lead.phone_status || '—'}</span>
                  {lead.phone_verified && <span className="text-xs text-emerald-400 font-medium">✓ Verified</span>}
                </div>
                {lead.line_type && <span className="text-xs text-slate-500">Type: {lead.line_type}</span>}
                {lead.phone_source && <span className="text-xs text-slate-500">[{lead.phone_source}]</span>}
              </div>
              <InfoRow label="LinkedIn" value={lead.linkedin_url} />
              <InfoRow label="Website" value={lead.company_website} />
            </div>
          </div>

          {/* Company Details */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><span>🏢</span> Company Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <InfoRow label="Company" value={lead.company_name} />
              <InfoRow label="Industry" value={lead.industry} />
              <InfoRow label="Employee Count" value={lead.employee_count} />
              <InfoRow label="Founding Year" value={lead.founding_year} />
              <InfoRow label="Source" value={lead.source} />
              <InfoRow label="Source URL" value={lead.source_url} />
              <InfoRow label="Scraped Date" value={lead.scraped_date ? new Date(lead.scraped_date).toLocaleDateString() : null} />
              <InfoRow label="Created" value={lead.created_at ? new Date(lead.created_at).toLocaleString() : null} />
            </div>
          </div>

          {/* Verification flags */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><span>✅</span> Verification</h2>
            <div className="flex flex-wrap gap-3">
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${lead.email_verified ? 'bg-emerald-900/30 border-emerald-700/40 text-emerald-300' : 'bg-slate-800/40 border-slate-700/40 text-slate-400'}`}>
                {lead.email_verified ? '✓' : '✗'} Email Verified
              </div>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${lead.phone_verified ? 'bg-emerald-900/30 border-emerald-700/40 text-emerald-300' : 'bg-slate-800/40 border-slate-700/40 text-slate-400'}`}>
                {lead.phone_verified ? '✓' : '✗'} Phone Verified
              </div>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${lead.role_verified ? 'bg-emerald-900/30 border-emerald-700/40 text-emerald-300' : 'bg-slate-800/40 border-slate-700/40 text-slate-400'}`}>
                {lead.role_verified ? '✓' : '✗'} Role Verified
              </div>
            </div>
          </div>

          {/* Evidence (Audit Trail) */}
          {evidence.length > 0 && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><span>🔍</span> Evidence Trail ({evidence.length})</h2>
              <div className="space-y-2">
                {evidence.map((e) => (
                  <div key={e.id} className="flex items-start gap-3 px-3 py-2 bg-surface-100 rounded-lg border border-slate-700/30">
                    <span className="text-xs text-slate-500 w-24 shrink-0 mt-0.5">{e.source}</span>
                    <span className="text-xs text-brand-300 w-28 shrink-0">{e.field_name}</span>
                    <span className="text-xs text-slate-300 break-all">{e.field_value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Outreach Audit Trail */}
          {audit_trail.length > 0 && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><span>📨</span> Outreach History ({audit_trail.length})</h2>
              <div className="space-y-3">
                {audit_trail.map((log) => (
                  <div key={log.id} className="p-3 bg-surface-100 rounded-lg border border-slate-700/30">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-medium text-white">{log.subject}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${log.status === 'Sent' ? 'text-emerald-300 bg-emerald-900/30' : 'text-slate-400 bg-slate-700/30'}`}>{log.status}</span>
                    </div>
                    <p className="text-xs text-slate-400">{log.created_at ? new Date(log.created_at).toLocaleString() : ''}</p>
                    {log.provider_message && <p className="text-xs text-slate-500 mt-1">{log.provider_message}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: Status + Email */}
        <div className="space-y-5">
          {/* Status Control */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Lead Status</h2>
            <select
              className="select mb-3"
              value={selectedStatus}
              onChange={e => setSelectedStatus(e.target.value)}
            >
              {STATUSES.map(s => <option key={s}>{s}</option>)}
            </select>
            <button
              onClick={handleStatusUpdate}
              disabled={statusUpdating || selectedStatus === lead.status}
              className="btn-primary w-full justify-center"
            >
              {statusUpdating ? 'Saving...' : 'Save Status'}
            </button>
          </div>

          {/* Cold Email */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Cold Email</h2>
            {!emailDraft ? (
              <button onClick={fetchEmail} disabled={loadingEmail} className="btn-secondary w-full justify-center">
                {loadingEmail ? 'Generating...' : '✉️ Generate Draft'}
              </button>
            ) : (
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Subject</p>
                  <p className="text-sm text-slate-200 font-medium">{emailDraft.subject}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Body</p>
                  <p className="text-xs text-slate-400 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">{emailDraft.body}</p>
                </div>
                <button onClick={sendEmail} className="btn-primary w-full justify-center text-xs">
                  📨 Send Email
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
