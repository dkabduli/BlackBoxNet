import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getIncidents, apiErrorMessage } from '../api/client';
import type { Incident } from '../types';
import IncidentCard from '../components/incidents/IncidentCard';
import { useScenario } from '../context/ScenarioContext';

export default function IncidentsPage() {
  const { activeScenarioId, activeScenario, ready, scenarioSwitching, refreshNonce } =
    useScenario();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchIncidents = useCallback(async () => {
    if (!ready || scenarioSwitching) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidents(activeScenarioId);
      setIncidents(data);
    } catch (e) {
      setError(apiErrorMessage(e, 'Failed to load incidents'));
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  }, [activeScenarioId, ready, scenarioSwitching]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents, refreshNonce]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Incidents</h1>
        <p className="text-sm text-gray-400">
          {activeScenario?.name ?? 'Incidents'} — outages with correlation analysis
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading || scenarioSwitching ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center text-gray-500">
          {scenarioSwitching ? 'Resetting scenario…' : 'Loading incidents…'}
        </div>
      ) : incidents.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center space-y-3">
          <p className="text-gray-500">
            No incidents yet. Run the simulation through <span className="text-blue-400 font-medium">T5</span> on
            the{' '}
            <Link to="/" className="text-blue-400 hover:underline">
              Dashboard
            </Link>{' '}
            to generate an outage incident.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {incidents.map((inc) => (
            <IncidentCard
              key={inc.id}
              incident={inc}
              onClick={() => navigate(`/incidents/${inc.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
