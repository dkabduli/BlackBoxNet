import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDevices, getIncidents } from '../api/client';
import type { Device, Incident } from '../types';
import DeviceCard from '../components/devices/DeviceCard';
import IncidentCard from '../components/incidents/IncidentCard';
import SimulationControls from '../components/simulation/SimulationControls';
import TopologyPreview from '../components/topology/TopologyPreview';

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [devData, incData] = await Promise.all([getDevices(), getIncidents()]);
      setDevices(devData || []);
      setIncidents(incData || []);
    } catch (e) {
      console.error('Failed to fetch dashboard data', e);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-sm text-gray-400">Network state replay platform — simulation mode</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Network Devices</h2>
            {devices.length === 0 ? (
              <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
                <p className="text-gray-500">No devices yet. Run a simulation step to begin.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <TopologyPreview devices={devices} highlightedDeviceId={incidents[0]?.root_device?.id} />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {devices.map((device) => (
                    <DeviceCard key={device.id} device={device} onClick={() => navigate('/devices')} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {incidents.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">Active Incidents</h2>
              <div className="space-y-3">
                {incidents.map((inc) => (
                  <IncidentCard
                    key={inc.id}
                    incident={inc}
                    onClick={() => navigate(`/incidents/${inc.id}`)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <div>
          <SimulationControls onStepComplete={fetchData} />
        </div>
      </div>
    </div>
  );
}
