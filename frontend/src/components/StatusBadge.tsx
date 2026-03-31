import type { RunStatus } from '../types'
import { cn } from '../lib/utils'

const statusConfig: Record<RunStatus, { label: string; className: string }> = {
  success: { label: 'Success', className: 'bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success)]/20' },
  failure: { label: 'Failure', className: 'bg-[var(--color-error-bg)] text-[var(--color-error)] border-[var(--color-error)]/20' },
  error: { label: 'Error', className: 'bg-[var(--color-error-bg)] text-[var(--color-error)] border-[var(--color-error)]/20' },
  running: { label: 'Running', className: 'bg-[var(--color-running-bg)] text-[var(--color-running)] border-[var(--color-running)]/20' },
}

export function StatusBadge({ status }: { status: RunStatus }) {
  const config = statusConfig[status]
  return (
    <span
      data-status={status}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        config.className,
      )}
    >
      {status === 'running' && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-running)] opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-running)]" />
        </span>
      )}
      {status !== 'running' && (
        <span className={cn('h-1.5 w-1.5 rounded-full', {
          'bg-[var(--color-success)]': status === 'success',
          'bg-[var(--color-error)]': status === 'failure' || status === 'error',
        })} />
      )}
      {config.label}
    </span>
  )
}
