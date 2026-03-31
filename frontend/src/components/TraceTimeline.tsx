import type { TraceEvent } from '../types'
import { TraceStep } from './TraceStep'

export function TraceTimeline({ events }: { events: TraceEvent[] }) {
  return (
    <div className="space-y-1.5">
      {events.map(event => (
        <TraceStep key={event.id} event={event} />
      ))}
    </div>
  )
}
