import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import LeadList from './pages/LeadList'
import LeadDetail from './pages/LeadDetail'
import ICPConfig from './pages/ICPConfig'
import PipelineStatus from './pages/PipelineStatus'
import ExportPage from './pages/ExportPage'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/companies', label: 'Companies', icon: '🏢' },
  { to: '/leads', label: 'Leads', icon: '👥' },
  { to: '/pipeline', label: 'Pipeline Status', icon: '⚡' },
  { to: '/icp', label: 'ICP Config', icon: '🎯' },
  { to: '/export', label: 'Export', icon: '📤' },
]

export default function App() {
  const location = useLocation()
  const isDetail = location.pathname.startsWith('/leads/')

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 flex flex-col border-r border-slate-700/40 bg-surface-50/50 backdrop-blur-xl">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700/40">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-brand-900/40">
            A
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">AutoNova</h1>
            <p className="text-xs text-slate-500">Lead Generation</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-link ${isActive || (to === '/leads' && isDetail) ? 'active' : ''}`
              }
            >
              <span className="text-base">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-slate-700/40">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="nav-link text-xs"
          >
            <span>📖</span>
            <span>API Docs</span>
          </a>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/leads" element={<LeadList />} />
          <Route path="/leads/:id" element={<LeadDetail />} />
          <Route path="/pipeline" element={<PipelineStatus />} />
          <Route path="/icp" element={<ICPConfig />} />
          <Route path="/export" element={<ExportPage />} />
        </Routes>
      </main>
    </div>
  )
}
