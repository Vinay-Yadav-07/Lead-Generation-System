import { useEffect, useState } from 'react'
import { getPipelineStatus } from '../api'

const STAGE_ICONS = {
  'database': '🏢',
  'globe': '🌐',
  'users': '👥',
  'badge-check': '✅',
  'star': '⭐',
  'thumbs-up': '🚀',
  'send': '📨',
}

const STAGE_COLORS = [
  'from-blue-700/30 to-blue-900/10 border-blue-700/40',
  'from-cyan-700/30 to-cyan-900/10 border-cyan-700/40',
  'from-brand-700/30 to-brand-900/10 border-brand-700/40',
  'from-amber-700/30 to-amber-900/10 border-amber-700/40',
  'from-emerald-700/30 to-emerald-900/10 border-emerald-700/40',
  'from-purple-700/30 to-purple-900/10 border-purple-700/40',
  'from-pink-700/30 to-pink-900/10 border-pink-700/40',
]

export default function PipelineStatus() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data: res } = await getPipelineStatus()
        setData(res)
      } catch {}
      setLoading(false)
    }
    fetch()
    const t = setInterval(fetch, 15000)
    return () => clearInterval(t)
  }, [])

  const stages = data?.stages || []
  const summary = data?.summary || {}

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Pipeline Status</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time view of your lead generation funnel</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Live updates every 15s
        </div>
      </div>

      {/* Funnel visualization */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-32 bg-slate-700/30 animate-pulse rounded-xl" />
          ))}
        </div>
      ) : stages.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-5xl mb-3">⚡</div>
          <p className="text-slate-400">No pipeline data yet. Run the pipeline from the Dashboard.</p>
        </div>
      ) : (
        <>
          {/* Stage Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {stages.map((stage, idx) => (
              <div
                key={stage.name}
                className={`pipeline-stage bg-gradient-to-br ${STAGE_COLORS[idx % STAGE_COLORS.length]} border`}
              >
                <div className="text-2xl">{STAGE_ICONS[stage.icon] || '📌'}</div>
                <div className="text-3xl font-bold text-white">{stage.count}</div>
                <div className="text-xs text-slate-400 text-center leading-tight">{stage.name}</div>
              </div>
            ))}
          </div>

          {/* Funnel flow chart */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-white mb-5 flex items-center gap-2">
              <span>📊</span> Conversion Funnel
            </h2>
            <div className="space-y-3">
              {stages.map((stage, idx) => {
                const maxCount = stages[0]?.count || 1
                const pct = maxCount > 0 ? Math.round((stage.count / maxCount) * 100) : 0
                const barColors = [
                  'bg-blue-500', 'bg-cyan-500', 'bg-brand-500',
                  'bg-amber-500', 'bg-emerald-500', 'bg-purple-500', 'bg-pink-500'
                ]
                return (
                  <div key={stage.name} className="flex items-center gap-4">
                    <div className="w-36 text-xs text-slate-400 text-right shrink-0">{stage.name}</div>
                    <div className="flex-1 h-6 bg-surface-100 rounded-lg overflow-hidden">
                      <div
                        className={`h-full ${barColors[idx % barColors.length]} rounded-lg transition-all duration-700 flex items-center px-2`}
                        style={{ width: `${Math.max(pct, 2)}%` }}
                      >
                        {pct > 10 && (
                          <span className="text-xs font-bold text-white">{stage.count}</span>
                        )}
                      </div>
                    </div>
                    <div className="w-12 text-xs text-slate-400 text-left shrink-0">{stage.count}</div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {Object.entries(summary).map(([key, val]) => (
              <div key={key} className="card p-3 text-center">
                <div className="text-xl font-bold text-white">{val}</div>
                <div className="text-xs text-slate-500 mt-0.5 capitalize">{key.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
