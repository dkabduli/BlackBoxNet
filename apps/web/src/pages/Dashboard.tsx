import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDevices, getIncidents, apiErrorMessage } from '../api/client';
import type { Device, Incident } from '../types';
import DeviceCard from '../components/devices/DeviceCard';
import IncidentCard from '../components/incidents/IncidentCard';
import SimulationControls from '../components/simulation/SimulationControls';
import ScenarioTabBar from '../components/simulation/ScenarioTabBar';
import LazyTopologyPreview from '../components/topology/LazyTopologyPreview';
import { useScenario } from '../context/ScenarioContext';
import { cn } from '../lib/utils';

export default function Dashboard() {
  const {
    activeScenarioId,
    activeScenario,
    ready,
    bootstrapError,
    scenarioSwitching,
    refreshNonce,
  } = useScenario();
  const [devices, setDevices] = useState<Device[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setFetchError(null);
    try {
      const [devData, incData] = await Promise.all([
        getDevices(activeScenarioId),
        getIncidents(activeScenarioId),
      ]);
      setDevices(devData);
      setIncidents(incData);
    } catch (e) {
      console.error('Failed to fetch dashboard data', e);
      setFetchError(apiErrorMessage(e, 'Failed to load dashboard data'));
    }
  }, [activeScenarioId]);

  useEffect(() => {
    if (ready && !scenarioSwitching) fetchData();
  }, [fetchData, ready, activeScenarioId, refreshNonce, scenarioSwitching]);

  const rootHostname = incidents[0]?.root_device?.hostname;
  const highlightedId = incidents[0]?.root_device?.id;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-sm text-gray-400">{activeScenario?.name ?? 'Select a scenario'}</p>
      </div>

      <ScenarioTabBar />

      {(bootstrapError || fetchError) && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-200">
          {bootstrapError ?? fetchError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Network Devices</h2>
            {!ready || scenarioSwitching ? (
              <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center text-gray-500">
                {scenarioSwitching ? 'Resetting scenario to T1…' : 'Loading…'}
              </div>
            ) : (
              <div className="space-y-4">
                {activeScenario?.topology?.links?.length ? (
                  <LazyTopologyPreview
                    devices={devices}
                    topology={activeScenario.topology}
                    topologyType={activeScenario.topology_type ?? 'linear'}
                    affectedSubnet={activeScenario.affected_subnet}
                    highlightedDeviceId={highlightedId}
                    highlightedHostname={rootHostname}
                    previewBeforeSimulation={devices.length === 0}
                  />
                ) : null}
                {devices.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-gray-700 bg-gray-900/30 px-4 py-3 text-center text-sm text-gray-400">
                    Device health cards appear after you run <span className="text-blue-400 font-medium">T1</span>.
                    Use the simulation panel to step through T1→T5.
                  </div>
                ) : scenarioSwitching ? (
                  <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-40 rounded-xl bg-gray-800/50 animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div
                    className={cn(
                      'grid gap-4',
                      devices.length >= 4
                        ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-4'
                        : 'grid-cols-1 md:grid-cols-3'
                    )}
                  >
                    {devices.map((device) => (
                      <DeviceCard
                        key={device.id}
                        device={device}
                        onClick={() => navigate('/devices')}
                      />
                    ))}
                  </div>
                )}
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
