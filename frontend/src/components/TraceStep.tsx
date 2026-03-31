import { useState } from 'react'
import type { TraceEvent } from '../types'
import { StatusBadge } from './StatusBadge'
import { formatDuration } from '../lib/utils'
import { ChevronRight, ChevronDown, Wrench, Brain, GitBranch, AlertCircle } from 'lucide-react'
import { cn } from '../lib/utils'

const stepTypeConfig: Record<string, { icon: React.ComponentType<{ className?: string }>; label: string; color: string }> = {
  tool_call: { icon: Wrench, label: 'Tool Call', color: 'text-blue-400' },
  llm_call: { icon: Brain, label: 'LLM Call', color: 'text-purple-400' },
  decision: { icon: GitBranch, label: 'Decision', color: 'text-amber-400' },
  error: { icon: AlertCircle, label: 'Error', color: 'text-red-400' },
  run_start: { icon: ChevronRight, label: 'Start', color: 'text-green-400' },
  run_end: { icon: ChevronRight, label: 'End', color: 'text-gray-400' },
}

function JsonBlock({ data, label }: { data: Record<string, unknown>; label: string }) {
  const str = JSON.stringify(data, null, 2)
  const truncated = str.length > 500
  const [expanded, setExpanded] = useState(false)

  if (Object.keys(data).length === 0) return null

  return (
    <div className="mt-2">
      <p className="text-[10px] uppercase tracking-wider text-[var(--color-text-dim)] mb-1">{label}</p>
      <pre className="rounded bg-[var(--color-bg)] p-2.5 text-xs text-[var(--color-text-muted)] overflow-x-auto leading-relaxed">
        {expanded || !truncated ? str : str.slice(0, 500) + '\n...'}
      </pre>
      {truncated && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs text-[var(--color-primary)] hover:underline"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  )
}

export function TraceStep({ event, depth = 0 }: { event: TraceEvent; depth?: number }) {
  const [isOpen, setIsOpen] = useState(
    event.status === 'failure' || event.status === 'error' || depth === 0
  )
  const config = stepTypeConfig[event.step_type] ?? stepTypeConfig.tool_call
  const Icon = config.icon
  const isError = event.status === 'failure' || event.status === 'error'
  const hasDetails = Object.keys(event.input).length > 0 || Object.keys(event.output).length > 0 || event.error_message

  return (
    <div data-testid="trace-step" data-status={event.status}>
      <div
        className={cn(
          'flex items-start gap-3 rounded-lg border px-4 py-3 transition-colors',
          isError
            ? 'border-[var(--color-error)]/30 bg-[var(--color-error-bg)]/50'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)]',
          hasDetails && 'cursor-pointer',
        )}
        onClick={() => hasDetails && setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 shrink-0 pt-0.5">
          {hasDetails ? (
            isOpen ? <ChevronDown className="h-3.5 w-3.5 text-[var(--color-text-dim)]" /> : <ChevronRight className="h-3.5 w-3.5 text-[var(--color-text-dim)]" />
          ) : (
            <span className="w-3.5" />
          )}
          <Icon className={cn('h-4 w-4', config.color)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn('text-[10px] uppercase tracking-wider font-medium', config.color)}>
              {config.label}
            </span>
            <span className="font-medium text-sm">{event.step_name}</span>
          </div>
          {isError && event.error_message && (
            <p className="text-sm text-[var(--color-error)] mt-1 break-words">{event.error_message}</p>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs tabular-nums text-[var(--color-text-dim)]">
            {formatDuration(event.duration_ms)}
          </span>
          <StatusBadge status={event.status} />
        </div>
      </div>

      {isOpen && hasDetails && (
        <div className="ml-6 mt-1 mb-1 pl-4 border-l-2 border-[var(--color-border-subtle)]">
          <JsonBlock data={event.input} label="Input" />
          <JsonBlock data={event.output} label="Output" />
          {isError && event.error_message && !Object.keys(event.input).length && (
            <div className="mt-2 rounded bg-[var(--color-error-bg)] p-2.5 text-sm text-[var(--color-error)]">
              {event.error_message}
            </div>
          )}
        </div>
      )}

      {event.children.length > 0 && (
        <div data-testid="trace-step-children" className="ml-6 mt-1 space-y-1 pl-4 border-l-2 border-[var(--color-border-subtle)]">
          {event.children.map(child => (
            <TraceStep key={child.id} event={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
