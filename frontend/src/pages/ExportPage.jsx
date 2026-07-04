import { useState } from 'react'
import { exportCSV, exportJSON } from '../api'

export default function ExportPage() {
  const [jsonLoading, setJsonLoading] = useState(false)
  const [jsonData, setJsonData] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleExportCSV = () => {
    const url = exportCSV()
    const a = document.createElement('a')
    a.href = url
    a.download = 'autonova_leads.csv'
    a.click()
  }

  const handleExportJSON = async () => {
    setJsonLoading(true)
    try {
      const { data } = await exportJSON()
      setJsonData(data)
    } catch {}
    setJsonLoading(false)
  }

  const handleCopy = () => {
    if (jsonData) {
      navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownloadJSON = () => {
    if (!jsonData) return
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'autonova_leads.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Export</h1>
        <p className="text-sm text-slate-400 mt-1">Download your leads in CSV or JSON format</p>
      </div>

      {/* Export options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* CSV Export */}
        <div className="card p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-900/40 border border-emerald-700/40 flex items-center justify-center text-xl">
              📊
            </div>
            <div>
              <h2 className="font-semibold text-white">CSV Export</h2>
              <p className="text-xs text-slate-400">Open in Excel, Google Sheets</p>
            </div>
          </div>
          <p className="text-sm text-slate-400">
            Downloads all leads as a CSV spreadsheet, including all enrichment fields, 
            verification status, and confidence scores.
          </p>
          <div className="flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Full Name</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Email + Status</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Phone + Verified</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Industry</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Confidence</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">+ 15 more fields</span>
          </div>
          <button
            id="export-csv-btn"
            onClick={handleExportCSV}
            className="btn-primary justify-center"
          >
            ⬇️ Download CSV
          </button>
        </div>

        {/* JSON Export */}
        <div className="card p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-900/40 border border-brand-700/40 flex items-center justify-center text-xl">
              🔧
            </div>
            <div>
              <h2 className="font-semibold text-white">JSON Export</h2>
              <p className="text-xs text-slate-400">For APIs, CRM integrations</p>
            </div>
          </div>
          <p className="text-sm text-slate-400">
            Exports all leads as a structured JSON array suitable for 
            importing into CRMs, webhooks, or custom integrations.
          </p>
          <div className="flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Full schema</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">Boolean flags</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">ISO timestamps</span>
            <span className="px-2 py-0.5 bg-surface-100 rounded border border-slate-700/40">All 22 fields</span>
          </div>
          <div className="flex gap-2">
            <button
              id="export-json-btn"
              onClick={handleExportJSON}
              disabled={jsonLoading}
              className="btn-primary flex-1 justify-center"
            >
              {jsonLoading ? '⏳ Loading...' : '⬇️ Load JSON'}
            </button>
            {jsonData && (
              <button
                onClick={handleDownloadJSON}
                className="btn-secondary justify-center"
              >
                💾 Save
              </button>
            )}
          </div>
        </div>
      </div>

      {/* JSON Preview */}
      {jsonData && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">
              JSON Preview <span className="text-slate-500">({jsonData.length} leads)</span>
            </h2>
            <div className="flex gap-2">
              <button onClick={handleCopy} className="btn-secondary text-xs">
                {copied ? '✓ Copied!' : '📋 Copy'}
              </button>
              <button onClick={handleDownloadJSON} className="btn-primary text-xs">
                ⬇️ Download
              </button>
            </div>
          </div>
          <pre className="text-xs text-slate-300 bg-surface-200 rounded-xl p-4 overflow-auto max-h-96 font-mono leading-relaxed border border-slate-700/40">
            {JSON.stringify(jsonData.slice(0, 3), null, 2)}
            {jsonData.length > 3 && `\n\n... and ${jsonData.length - 3} more leads`}
          </pre>
        </div>
      )}
    </div>
  )
}
