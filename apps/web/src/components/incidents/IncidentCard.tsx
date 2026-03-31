import { AlertTriangle, Clock, Server } from 'lucide-react';
import type { Incident } from '../../types';
import { formatTimestamp } from '../../lib/utils';

interface Props {
  incident: Incident;
  onClick?: () => void;
}

export default function IncidentCard({ incident, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className="rounded-xl border border-red-500/30 bg-red-500/5 p-5 cursor-pointer hover:ring-1 hover:ring-red-500/50 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="font-semibold text-white text-sm">{incident.title}</h3>
        </div>
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 uppercase">
          {incident.status}
        </span>
      </div>

      {incident.suspicion_summary && (
        <p className="text-xs text-gray-300 mb-3 line-clamp-2">{incident.suspicion_summary}</p>
      )}

      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatTimestamp(incident.start_time)}
        </span>
        <span className="flex items-center gap-1">
          <Server className="w-3 h-3" />
          {incident.affected_device_count} devices
        </span>
        <span>{incident.event_count} events</span>
      </div>
    </div>
  );
}
