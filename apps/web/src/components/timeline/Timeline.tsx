import { useState } from 'react';
import { ChevronLeft, ChevronRight, FileCode, AlertTriangle, Shield } from 'lucide-react';
import type { TimelineEvent } from '../../types';
import { severityColor, formatTimestamp, cn } from '../../lib/utils';

interface Props {
  events: TimelineEvent[];
  onEventClick?: (event: TimelineEvent) => void;
}

function eventIcon(type: string) {
  switch (type) {
    case 'CONFIG_CHANGE': return FileCode;
    case 'OUTAGE_STARTED': return AlertTriangle;
    default: return Shield;
  }
}

function EventCard({ event, onClick }: { event: TimelineEvent; onClick?: () => void }) {
  const Icon = eventIcon(event.event_type);

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative pl-8 pb-6 cursor-pointer group',
        'before:absolute before:left-3 before:top-6 before:w-px before:h-full before:bg-gray-700'
      )}
    >
      <div className={cn(
        'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center border',
        severityColor(event.severity),
        event.is_primary_cause && 'ring-2 ring-orange-400/50'
      )}>
        <Icon className="w-3 h-3" />
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-3 group-hover:border-gray-600 transition-colors">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-medium', severityColor(event.severity))}>
              {event.severity}
            </span>
            <h4 className="text-sm font-medium text-white">{event.title}</h4>
          </div>
          <span className="text-[10px] text-gray-500 font-mono">{formatTimestamp(event.timestamp)}</span>
        </div>

        <p className="text-xs text-gray-400 mb-2">{event.description}</p>

        <div className="flex items-center gap-3 text-[10px] text-gray-500">
          <span className="font-mono">{event.device_hostname}</span>
          <span className="px-1.5 py-0.5 bg-gray-800 rounded">{event.event_type}</span>
          {event.is_primary_cause && (
            <span className="px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded font-medium">PRIMARY SUSPECT</span>
          )}
          {event.config_diff && (
            <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded">View Diff</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Timeline({ events, onEventClick }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0);

  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No events yet. Run simulation steps to generate events.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Event Timeline ({events.length} events)</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
            disabled={currentIdx === 0}
            className="p-1 rounded hover:bg-gray-800 disabled:opacity-30 text-gray-400"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-gray-400">
            {currentIdx + 1} / {events.length}
          </span>
          <button
            onClick={() => setCurrentIdx(Math.min(events.length - 1, currentIdx + 1))}
            disabled={currentIdx >= events.length - 1}
            className="p-1 rounded hover:bg-gray-800 disabled:opacity-30 text-gray-400"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-0">
        {events.map((event, i) => (
          <EventCard key={event.id} event={event} onClick={() => { setCurrentIdx(i); onEventClick?.(event); }} />
        ))}
      </div>
    </div>
  );
}
