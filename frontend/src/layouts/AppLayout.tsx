import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard, ArrowLeftRight, Wallet, Target, TrendingUp, Upload,
  LineChart, FileText, Settings, Menu, X, Moon, Sun, LogOut,
} from 'lucide-react'
import { useAuth } from '@/features/authentication/AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/imports', label: 'Import Centre', icon: Upload },
  { to: '/budgets', label: 'Budgets', icon: Wallet },
  { to: '/goals', label: 'Savings Goals', icon: Target },
  { to: '/investments', label: 'Investments', icon: TrendingUp },
  { to: '/forecasts', label: 'Forecasts', icon: LineChart },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [dark, setDark] = useState(false)
  const { signOut, isDemoMode } = useAuth()

  const toggleDark = () => {
    setDark((d) => !d)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <div className="flex min-h-screen bg-ink-50 dark:bg-ink-900">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col border-r border-ink-100 dark:border-ink-800 bg-white dark:bg-ink-800 px-4 py-6">
        <SidebarContent onNavigate={() => {}} />
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 bg-white dark:bg-ink-800 px-4 py-6">
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between border-b border-ink-100 dark:border-ink-800 bg-white dark:bg-ink-800 px-4 py-3 lg:px-8">
          <button className="lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex-1" />
          {isDemoMode && (
            <span className="mr-4 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
              Demo Mode
            </span>
          )}
          <button onClick={toggleDark} className="btn-secondary !px-2.5" aria-label="Toggle dark mode">
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button onClick={() => signOut()} className="btn-secondary ml-2 !px-2.5" aria-label="Sign out">
            <LogOut className="h-4 w-4" />
          </button>
        </header>
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
        {/* Mobile bottom nav */}
        <nav className="lg:hidden flex justify-around border-t border-ink-100 dark:border-ink-800 bg-white dark:bg-ink-800 py-2">
          {NAV_ITEMS.slice(0, 5).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-2 py-1 text-xs ${isActive ? 'text-brand-600' : 'text-ink-400'}`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label.split(' ')[0]}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}

function SidebarContent({ onNavigate }: { onNavigate: () => void }) {
  return (
    <>
      <div className="flex items-center gap-2 px-2 pb-8">
        <img src="/logo.svg" alt="ExpenseCast" className="h-8 w-8" />
        <span className="text-lg font-bold text-ink-800 dark:text-white">ExpenseCast</span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300'
                  : 'text-ink-600 hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-700'
              }`
            }
          >
            <item.icon className="h-4.5 w-4.5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </>
  )
}
