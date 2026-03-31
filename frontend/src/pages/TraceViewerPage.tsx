import { useParams, Link } from 'react-router-dom'
import { getRunDetail } from '../data/mock'
import { TraceTimeline } from '../components/TraceTimeline'
import { StatusBadge } from '../components/StatusBadge'
import { formatDuration, formatTimestamp } from '../lib/utils'
import { ArrowLeft, Clock, Layers, Calendar } from 'lucide-react'

export function TraceViewerPage() {
  const { runId } = useParams<{ runId: string }>()
  const detail = runId ? getRunDetail(runId) : null

  if (!detail) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-[var(--color-text-muted)]">Run not found</p>
        <Link to="/" className="mt-3 text-sm text-[var(--color-primary)] hover:underline">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const { run, events } = detail

  return (
    <div className="space-y-5">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to dashboard
      </Link>

      <div data-testid="run-header" className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-semibold">{run.agent_name}</h1>
              <StatusBadge status={run.status} />
            </div>
            <p className="text-xs text-[var(--color-text-dim)] mt-1 font-mono">{run.id}</p>
          </div>
          {run.metadata && Object.keys(run.metadata).length > 0 && (
            <div className="flex gap-2">
              {Object.entries(run.metadata).map(([key, value]) => (
                <span key={key} className="rounded bg-[var(--color-bg)] px-2 py-0.5 text-xs text-[var(--color-text-muted)]">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center gap-6 text-sm text-[var(--color-text-muted)]">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            {formatTimestamp(run.started_at)}
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            {formatDuration(run.duration_ms)}
          </div>
          <div className="flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5" />
            {run.step_count} steps
          </div>
        </div>

        {run.error_message && (
          <div className="mt-3 rounded bg-[var(--color-error-bg)] border border-[var(--color-error)]/20 p-3 text-sm text-[var(--color-error)]">
            {run.error_message}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">Execution Trace</h2>
        <TraceTimeline events={events} />
      </div>
    </div>
  )
}
