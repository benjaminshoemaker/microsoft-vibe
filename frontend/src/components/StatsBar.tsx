import type { RunStats } from '../types'
import { formatDuration } from '../lib/utils'
import { Activity, AlertTriangle, Clock, TrendingUp } from 'lucide-react'

interface StatsBarProps {
  stats: RunStats
}

function StatCard({ icon: Icon, label, value, subValue, variant }: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  subValue?: string
  variant?: 'default' | 'success' | 'error'
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <div className={`rounded-md p-2 ${
        variant === 'success' ? 'bg-[var(--color-success-bg)]' :
        variant === 'error' ? 'bg-[var(--color-error-bg)]' :
        'bg-[var(--color-primary)]/10'
      }`}>
        <Icon className={`h-4 w-4 ${
          variant === 'success' ? 'text-[var(--color-success)]' :
          variant === 'error' ? 'text-[var(--color-error)]' :
          'text-[var(--color-primary)]'
        }`} />
      </div>
      <div>
        <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
        <p className="text-lg font-semibold leading-tight">{value}</p>
        {subValue && <p className="text-xs text-[var(--color-text-dim)]">{subValue}</p>}
      </div>
    </div>
  )
}

export function StatsBar({ stats }: StatsBarProps) {
  return (
    <div data-testid="stats-bar" className="grid grid-cols-4 gap-3">
      <StatCard
        icon={Activity}
        label="Total Runs"
        value={stats.total_runs.toString()}
        subValue="last 24 hours"
      />
      <StatCard
        icon={TrendingUp}
        label="Success"
        value={stats.success_count.toString()}
        variant="success"
      />
      <StatCard
        icon={AlertTriangle}
        label="Failure Rate"
        value={`${stats.failure_rate}%`}
        subValue={`${stats.failure_count} failed`}
        variant={stats.failure_rate > 15 ? 'error' : 'default'}
      />
      <StatCard
        icon={Clock}
        label="Avg Duration"
        value={formatDuration(stats.avg_duration_ms)}
      />
    </div>
  )
}
