import { useNavigate } from 'react-router-dom'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import { useState } from 'react'
import type { Run } from '../types'
import { StatusBadge } from './StatusBadge'
import { formatDuration, formatTimestamp } from '../lib/utils'
import { ArrowUpDown, ChevronDown, ChevronUp } from 'lucide-react'

const columnHelper = createColumnHelper<Run>()

const columns = [
  columnHelper.accessor('agent_name', {
    header: 'Agent',
    cell: info => (
      <span className="font-medium text-[var(--color-text)]">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: info => <StatusBadge status={info.getValue()} />,
  }),
  columnHelper.accessor('started_at', {
    header: 'Started',
    cell: info => (
      <span className="text-[var(--color-text-muted)] text-sm">{formatTimestamp(info.getValue())}</span>
    ),
  }),
  columnHelper.accessor('duration_ms', {
    header: 'Duration',
    cell: info => (
      <span className="text-sm tabular-nums">{formatDuration(info.getValue())}</span>
    ),
  }),
  columnHelper.accessor('step_count', {
    header: 'Steps',
    cell: info => (
      <span className="text-sm tabular-nums text-[var(--color-text-muted)]">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('error_message', {
    header: 'Error',
    cell: info => {
      const msg = info.getValue()
      if (!msg) return <span className="text-[var(--color-text-dim)]">—</span>
      return (
        <span className="text-sm text-[var(--color-error)] truncate max-w-[300px] block" title={msg}>
          {msg}
        </span>
      )
    },
  }),
]

export function RunsTable({ runs }: { runs: Run[] }) {
  const navigate = useNavigate()
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'started_at', desc: true },
  ])

  const table = useReactTable({
    data: runs,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <table className="w-full">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id} className="border-b border-[var(--color-border)]">
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === 'asc' ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : header.column.getIsSorted() === 'desc' ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ArrowUpDown className="h-3 w-3 opacity-30" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr
              key={row.id}
              data-status={row.original.status}
              onClick={() => navigate(`/runs/${row.original.id}`)}
              className={`border-b border-[var(--color-border-subtle)] cursor-pointer transition-colors hover:bg-[var(--color-surface-hover)] ${
                row.original.status === 'failure' || row.original.status === 'error'
                  ? 'bg-[var(--color-error-bg)]/30'
                  : ''
              }`}
            >
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
