import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getDevices, apiErrorMessage } from '../api/client';
import type { Device } from '../types';
import DeviceCard from '../components/devices/DeviceCard';
import LazyTopologyPreview from '../components/topology/LazyTopologyPreview';
import { useScenario } from '../context/ScenarioContext';

export default function DevicesPage() {
  const { activeScenarioId, activeScenario, ready, scenarioSwitching, refreshNonce } =
    useScenario();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    if (!ready || scenarioSwitching) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getDevices(activeScenarioId);
      setDevices(data);
    } catch (e) {
      setError(apiErrorMessage(e, 'Failed to load devices'));
      setDevices([]);
    } finally {
      setLoading(false);
    }
  }, [activeScenarioId, ready, scenarioSwitching]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices, refreshNonce]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Network Devices</h1>
        <p className="text-sm text-gray-400">
          {activeScenario?.name ?? 'Devices'} — latest health for the active scenario
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading || scenarioSwitching ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center text-gray-500">
          {scenarioSwitching ? 'Resetting scenario…' : 'Loading devices…'}
        </div>
      ) : devices.length === 0 ? (
        <div className="space-y-4">
          {activeScenario?.topology?.links?.length ? (
            <LazyTopologyPreview
              devices={[]}
              topology={activeScenario.topology}
              topologyType={activeScenario.topology_type}
              affectedSubnet={activeScenario.affected_subnet}
              scenarioDescription={activeScenario.description}
              previewBeforeSimulation
            />
          ) : null}
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center space-y-3">
            <p className="text-gray-500">
              No devices yet. Run <span className="text-blue-400 font-medium">T1</span> on the{' '}
              <Link to="/" className="text-blue-400 hover:underline">
                Dashboard
              </Link>{' '}
              to populate device health cards (T1→T5).
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {activeScenario?.topology?.links?.length ? (
            <LazyTopologyPreview
              devices={devices}
              topology={activeScenario.topology}
              topologyType={activeScenario.topology_type}
              affectedSubnet={activeScenario.affected_subnet}
              scenarioDescription={activeScenario.description}
            />
          ) : null}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.map((device) => (
              <DeviceCard key={device.id} device={device} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
