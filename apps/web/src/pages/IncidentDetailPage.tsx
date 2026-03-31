import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Shield, Lightbulb } from 'lucide-react';
import { getIncident, getIncidentTimeline, getIncidentCorrelation } from '../api/client';
import type { Incident, TimelineEvent, CorrelationData } from '../types';
import Timeline from '../components/timeline/Timeline';
import ConfigDiffViewer from '../components/config/ConfigDiffViewer';
import { suspicionColor, cn } from '../lib/utils';

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [correlation, setCorrelation] = useState<CorrelationData | null>(null);
  const [selectedDiff, setSelectedDiff] = useState<{ deviceId: string; diffId: string } | null>(null);

  useEffect(() => {
    if (!id) return;
    getIncident(id).then(setIncident).catch(console.error);
    getIncidentTimeline(id).then((data) => setEvents(data?.events || [])).catch(console.error);
    getIncidentCorrelation(id).then(setCorrelation).catch(console.error);
  }, [id]);

  const handleEventClick = (event: TimelineEvent) => {
    if (event.config_diff?.diff_id) {
      setSelectedDiff({ deviceId: event.device_id, diffId: event.config_diff.diff_id });
    }
  };

  if (!incident) {
    return <div className="text-center py-12 text-gray-500">Loading incident...</div>;
  }

  return (
    <div className="space-y-6">
      <Link to="/incidents" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Incidents
      </Link>

      <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            <div>
              <h1 className="text-xl font-bold text-white">{incident.title}</h1>
              <p className="text-sm text-gray-400 mt-0.5">{incident.affected_scope}</p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-500/20 text-red-400 uppercase">
            {incident.status}
          </span>
        </div>

        {incident.root_device && (
          <p className="text-xs text-gray-400">
            Root device: <span className="text-white font-medium">{incident.root_device.hostname}</span>
          </p>
        )}
      </div>

      {correlation && (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-orange-400" />
            <h2 className="font-semibold text-white">Correlation Analysis</h2>
          </div>

          {correlation.suspicion_summary && (
            <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/30">
              <p className="text-sm text-orange-200">{correlation.suspicion_summary}</p>
            </div>
          )}

          <div className="space-y-2">
            {correlation.correlation_flags.map((flag, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-800/50">
                <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-bold uppercase', suspicionColor(flag.suspicion_level))}>
                  {flag.suspicion_level}
                </span>
                <div>
                  <p className="text-sm text-white">{flag.description}</p>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">{flag.rule}</p>
                </div>
              </div>
            ))}
          </div>

          {correlation.recommendation && (
            <div className="flex items-start gap-2 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
              <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-200">{correlation.recommendation}</p>
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <Timeline events={events} onEventClick={handleEventClick} />
      </div>

      {selectedDiff && (
        <ConfigDiffViewer
          deviceId={selectedDiff.deviceId}
          diffId={selectedDiff.diffId}
          onClose={() => setSelectedDiff(null)}
        />
      )}
    </div>
  );
}
