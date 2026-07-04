import { useEffect, useState } from 'react'
import { getICP, updateICP } from '../api'

const DEFAULT_ICP = {
  job_titles: ['CEO', 'Founder', 'CTO', 'Director'],
  industry: 'Logistics',
  country: 'India',
  company_size: '10-500',
  employee_min: 10,
  employee_max: 500,
  founding_year: 2010,
}

export default function ICPConfig() {
  const [icp, setIcp] = useState(DEFAULT_ICP)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await getICP()
        // Merge loaded data with defaults
        setIcp(prev => ({ ...prev, ...data }))
      } catch {}
      setLoading(false)
    }
    fetch()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      // Parse job_titles if stored as string (textarea)
      const payload = {
        ...icp,
        job_titles: typeof icp.job_titles === 'string'
          ? icp.job_titles.split('\n').map(s => s.trim()).filter(Boolean)
          : icp.job_titles,
      }
      await updateICP(payload)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Save failed.')
    }
    setSaving(false)
  }

  const setField = (key, val) => setIcp(prev => ({ ...prev, [key]: val }))

  const titlesStr = Array.isArray(icp.job_titles) ? icp.job_titles.join('\n') : icp.job_titles

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-40 bg-slate-700/40 animate-pulse rounded" />
        <div className="card p-6 space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-10 bg-slate-700/40 animate-pulse rounded" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">ICP Configuration</h1>
        <p className="text-sm text-slate-400 mt-1">Define your Ideal Customer Profile to guide lead discovery</p>
      </div>

      <div className="card p-6 space-y-5">
        {/* Industry */}
        <div>
          <label htmlFor="icp-industry" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Industry
          </label>
          <input
            id="icp-industry"
            type="text"
            className="input"
            placeholder="e.g. Logistics, SaaS, FinTech"
            value={icp.industry || ''}
            onChange={e => setField('industry', e.target.value)}
          />
        </div>

        {/* Country */}
        <div>
          <label htmlFor="icp-country" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Country / Geography
          </label>
          <input
            id="icp-country"
            type="text"
            className="input"
            placeholder="e.g. India, USA"
            value={icp.country || ''}
            onChange={e => setField('country', e.target.value)}
          />
        </div>

        {/* Company Size */}
        <div>
          <label htmlFor="icp-company-size" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Company Size Range
          </label>
          <input
            id="icp-company-size"
            type="text"
            className="input"
            placeholder="e.g. 10-500"
            value={icp.company_size || ''}
            onChange={e => setField('company_size', e.target.value)}
          />
          <p className="text-xs text-slate-500 mt-1">Or set specific min/max below</p>
        </div>

        {/* Employee Min / Max */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="icp-min" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Min Employees
            </label>
            <input
              id="icp-min"
              type="number"
              min="0"
              className="input"
              value={icp.employee_min ?? 0}
              onChange={e => setField('employee_min', parseInt(e.target.value) || 0)}
            />
          </div>
          <div>
            <label htmlFor="icp-max" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Max Employees
            </label>
            <input
              id="icp-max"
              type="number"
              min="0"
              className="input"
              value={icp.employee_max ?? 10000}
              onChange={e => setField('employee_max', parseInt(e.target.value) || 10000)}
            />
          </div>
        </div>

        {/* Founding Year — NEW field from spec */}
        <div>
          <label htmlFor="icp-founding-year" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Founded After Year <span className="text-brand-400 font-normal normal-case">(optional)</span>
          </label>
          <input
            id="icp-founding-year"
            type="number"
            min="1900"
            max={new Date().getFullYear()}
            className="input"
            placeholder="e.g. 2010"
            value={icp.founding_year || ''}
            onChange={e => setField('founding_year', parseInt(e.target.value) || null)}
          />
        </div>

        {/* Job Titles */}
        <div>
          <label htmlFor="icp-titles" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Target Job Titles <span className="text-slate-500 font-normal">(one per line)</span>
          </label>
          <textarea
            id="icp-titles"
            rows="5"
            className="input resize-none"
            placeholder="CEO&#10;Founder&#10;CTO&#10;Director"
            value={titlesStr}
            onChange={e => setField('job_titles', e.target.value)}
          />
        </div>

        {/* Save */}
        {error && (
          <div className="px-3 py-2 bg-red-900/30 border border-red-700/40 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}
        <button
          id="save-icp-btn"
          onClick={handleSave}
          disabled={saving}
          className={`btn-primary w-full justify-center ${saved ? 'bg-emerald-600 hover:bg-emerald-500' : ''}`}
        >
          {saving ? 'Saving...' : saved ? '✓ Saved!' : '💾 Save ICP Configuration'}
        </button>
      </div>
    </div>
  )
}
