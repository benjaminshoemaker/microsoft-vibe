import { NavLink, Outlet } from 'react-router-dom'
import { Activity, Bell, Eye } from 'lucide-react'
import { cn } from '../lib/utils'

function NavItem({ to, icon: Icon, label }: { to: string; icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) => cn(
        'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
        isActive
          ? 'bg-[var(--color-surface)] text-[var(--color-text)]'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)]',
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </NavLink>
  )
}

export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-bg)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Eye className="h-5 w-5 text-[var(--color-primary)]" />
              <span className="font-semibold text-sm tracking-tight">Agent Observatory</span>
            </div>
            <nav className="flex items-center gap-1">
              <NavItem to="/" icon={Activity} label="Dashboard" />
              <NavItem to="/alerts" icon={Bell} label="Alerts" />
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-[var(--color-success-bg)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-success)] border border-[var(--color-success)]/20">
              Mock Data
            </span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  )
}
