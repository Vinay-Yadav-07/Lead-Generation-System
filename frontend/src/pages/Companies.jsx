import { useEffect, useState } from 'react'
import { getCompanies } from '../api'

export default function Companies() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedCompany, setSelectedCompany] = useState(null)

  const fetchCompanies = async () => {
    setLoading(true)
    try {
      const { data } = await getCompanies()
      setCompanies(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchCompanies()
  }, [])

  const filteredCompanies = companies.filter(c => {
    const term = search.toLowerCase()
    return (
      (c.company_name || '').toLowerCase().includes(term) ||
      (c.industry || '').toLowerCase().includes(term) ||
      (c.country || '').toLowerCase().includes(term)
    )
  })

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white font-sans">Discovered Companies</h1>
          <p className="text-sm text-slate-400 mt-1">
            {filteredCompanies.length} compan{filteredCompanies.length !== 1 ? 'ies' : 'y'} matching criteria
          </p>
        </div>
        <button onClick={fetchCompanies} className="btn-secondary text-xs">
          🔄 Refresh List
        </button>
      </div>

      {/* Search Input */}
      <div className="card p-4">
        <div className="relative max-w-md">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">🔍</span>
          <input
            id="company-search"
            type="search"
            placeholder="Search by name, industry, or country..."
            className="input pl-9"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Companies Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 space-y-3">
            <div className="h-6 w-1/3 bg-slate-700/40 animate-pulse rounded" />
            <div className="h-10 bg-slate-700/30 animate-pulse rounded" />
            <div className="h-10 bg-slate-700/30 animate-pulse rounded" />
            <div className="h-10 bg-slate-700/30 animate-pulse rounded" />
          </div>
        ) : filteredCompanies.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            No companies found. Run the "Discover Companies" task from the dashboard.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-slate-700/50 text-slate-400 uppercase tracking-wider text-xs font-semibold">
                  <th className="px-6 py-4">Company Name</th>
                  <th className="px-6 py-4">Website</th>
                  <th className="px-6 py-4">Industry</th>
                  <th className="px-6 py-4">Country</th>
                  <th className="px-6 py-4 text-center">Confidence</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map(c => {
                  const hasWebsite = !!(c.website && c.website.trim())
                  return (
                    <tr key={c.id} className="table-row">
                      <td className="px-6 py-4 font-semibold text-white">{c.company_name}</td>
                      <td className="px-6 py-4">
                        {hasWebsite ? (
                          <a
                            href={c.website}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-300 hover:underline"
                            onClick={e => e.stopPropagation()}
                          >
                            {c.website.replace(/^https?:\/\//, '')}
                          </a>
                        ) : (
                          <span className="text-slate-500 italic">No website</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-300">{c.industry || '—'}</td>
                      <td className="px-6 py-4 text-slate-300">{c.country || '—'}</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`pill ${c.confidence_score >= 8 ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-slate-800 text-slate-300 border-slate-700'} border px-2 py-0.5 rounded text-xs`}>
                          {c.confidence_score?.toFixed(1) || '0.0'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`badge ${hasWebsite ? 'badge-approved' : 'badge-new'}`}>
                          {hasWebsite ? 'Website Found' : 'Discovered'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setSelectedCompany(c)}
                          className="btn-secondary text-xs py-1 px-3"
                        >
                          👁️ View
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Company Details Modal */}
      {selectedCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="card w-full max-w-xl p-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setSelectedCompany(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold"
            >
              ✕
            </button>
            <h2 className="text-xl font-bold text-white mb-4">Company Details</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Company Name</span>
                  <span className="text-sm font-semibold text-slate-200">{selectedCompany.company_name}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Website</span>
                  {selectedCompany.website ? (
                    <a
                      href={selectedCompany.website}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-semibold text-brand-300 hover:underline block"
                    >
                      {selectedCompany.website}
                    </a>
                  ) : (
                    <span className="text-sm text-slate-500 italic block">None</span>
                  )}
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Industry</span>
                  <span className="text-sm text-slate-200 block">{selectedCompany.industry || '—'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Country</span>
                  <span className="text-sm text-slate-200 block">{selectedCompany.country || '—'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Employee Count</span>
                  <span className="text-sm text-slate-200 block">{selectedCompany.employee_count ?? '—'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Founded Year</span>
                  <span className="text-sm text-slate-200 block">{selectedCompany.founded || '—'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Confidence Score</span>
                  <span className="text-sm text-slate-200 block font-mono">{selectedCompany.confidence_score?.toFixed(1) || '0.0'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">LinkedIn URL</span>
                  {selectedCompany.linkedin_url ? (
                    <a
                      href={selectedCompany.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-semibold text-brand-300 hover:underline block"
                    >
                      LinkedIn Page
                    </a>
                  ) : (
                    <span className="text-sm text-slate-500 italic block">None</span>
                  )}
                </div>
              </div>
              <div className="border-t border-slate-700/50 pt-4">
                <span className="text-xs text-slate-500 uppercase tracking-wider block">Discovery Source</span>
                <span className="text-sm text-slate-300 block">{selectedCompany.source || '—'}</span>
              </div>
              {selectedCompany.founder && (
                <div className="border-t border-slate-700/50 pt-4">
                  <span className="text-xs text-slate-500 uppercase tracking-wider block">Known Founder/Contact</span>
                  <span className="text-sm text-slate-200 block">{selectedCompany.founder}</span>
                </div>
              )}
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedCompany(null)}
                className="btn-primary px-5 py-2 text-xs"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
