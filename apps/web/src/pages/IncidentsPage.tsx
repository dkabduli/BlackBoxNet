import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncidents } from '../api/client';
import type { Incident } from '../types';
import IncidentCard from '../components/incidents/IncidentCard';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    getIncidents().then(setIncidents).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Incidents</h1>
        <p className="text-sm text-gray-400">Network outages and failures with correlation analysis</p>
      </div>

      {incidents.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
          <p className="text-gray-500">No incidents yet. Run the simulation through T5 to generate an outage incident.</p>
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
