import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Shield, Lightbulb, FileSearch } from 'lucide-react';
import {
  getIncident,
  getIncidentTimeline,
  getIncidentCorrelation,
  getDevices,
  apiErrorMessage,
} from '../api/client';
import type { Incident, TimelineEvent, CorrelationData, Device } from '../types';
import Timeline from '../components/timeline/Timeline';
import ConfigDiffViewer from '../components/config/ConfigDiffViewer';
import { suspicionColor, cn } from '../lib/utils';
import TopologyPreview from '../components/topology/TopologyPreview';
import { useScenario } from '../context/ScenarioContext';

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { activeScenario, scenarios } = useScenario();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [correlation, setCorrelation] = useState<CorrelationData | null>(null);
  const [selectedDiff, setSelectedDiff] = useState<{ deviceId: string; diffId: string } | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      setError('No incident ID in URL.');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setIncident(null);

    (async () => {
      try {
        const inc = await getIncident(id);
        if (cancelled) return;
        setIncident(inc);

        const scenarioId = inc.scenario_id ?? activeScenario?.id;
        const [timelineData, corr, devs] = await Promise.all([
          getIncidentTimeline(id),
          getIncidentCorrelation(id).catch(() => null),
          getDevices(scenarioId),
        ]);
        if (cancelled) return;
        setEvents(timelineData?.events ?? []);
        setCorrelation(corr);
        setDevices(devs);
      } catch (e) {
        if (!cancelled) {
          setError(apiErrorMessage(e, 'Failed to load incident'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id, activeScenario?.id]);

  const handleEventClick = (event: TimelineEvent) => {
    if (event.config_diff?.diff_id) {
      setSelectedDiff({ deviceId: event.device_id, diffId: event.config_diff.diff_id });
    }
  };

  if (!id) {
    return (
      <div className="text-center py-12 text-gray-500">
        Invalid incident link. <Link to="/incidents" className="text-blue-400 hover:underline">Back to Incidents</Link>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading incident…</div>;
  }

  if (error || !incident) {
    return (
      <div className="space-y-4 text-center py-12">
        <p className="text-red-300">{error ?? 'Incident not found.'}</p>
        <Link to="/incidents" className="text-blue-400 hover:underline text-sm">
          Back to Incidents
        </Link>
      </div>
    );
  }

  const scenarioMeta = scenarios.find((s) => s.id === incident.scenario_id) ?? activeScenario;

  const rootCauseEvent =
    events.find((event) => event.is_primary_cause && event.config_diff?.diff_id) ??
    events.find((event) => event.config_diff?.diff_id);
  const rootDevice = devices.find((device) => device.id === incident.root_device?.id);
  const rootDeviceUsesLiveSsh = rootDevice?.latest_snapshot?.snapshot_source === 'ssh';

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

          {correlation.correlation_flags?.length > 0 && (
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
          )}

          {correlation.recommendation && (
            <div className="flex items-start gap-2 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
              <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-200">{correlation.recommendation}</p>
            </div>
          )}
        </div>
      )}

      {(devices.length > 0 || scenarioMeta?.topology?.links?.length) && (
        <TopologyPreview
          devices={devices}
          topology={scenarioMeta?.topology}
          topologyType={scenarioMeta?.topology_type}
          affectedSubnet={scenarioMeta?.affected_subnet}
          highlightedDeviceId={incident.root_device?.id}
          highlightedHostname={incident.root_device?.hostname}
        />
      )}

      {rootCauseEvent && (
        <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileSearch className="h-5 w-5 text-purple-400" />
                <h2 className="font-semibold text-white">Root Cause Config Mismatch</h2>
              </div>
              <p className="text-sm text-gray-300">
                {rootCauseEvent.config_diff?.summary || rootCauseEvent.description || 'A config change is the primary suspect for this outage.'}
              </p>
              <div className="flex flex-wrap gap-2 text-xs text-gray-400">
                <span className="rounded bg-gray-800 px-2 py-1">{rootCauseEvent.device_hostname}</span>
                <span className="rounded bg-gray-800 px-2 py-1">{rootCauseEvent.event_type}</span>
                {rootDeviceUsesLiveSsh && (
                  <span className="rounded bg-blue-500/20 px-2 py-1 text-blue-300">live ssh config</span>
                )}
                {rootCauseEvent.config_diff?.suspicion_level && (
                  <span className={cn('rounded px-2 py-1 font-medium', suspicionColor(rootCauseEvent.config_diff.suspicion_level))}>
                    {rootCauseEvent.config_diff.suspicion_level.toUpperCase()} suspicion
                  </span>
                )}
              </div>
            </div>
            {rootCauseEvent.config_diff?.diff_id && (
              <button
                onClick={() =>
                  setSelectedDiff({
                    deviceId: rootCauseEvent.device_id,
                    diffId: rootCauseEvent.config_diff!.diff_id,
                  })
                }
                className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-500"
              >
                View Root Cause Diff
              </button>
            )}
          </div>
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
