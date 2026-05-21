import axios from 'axios';

/** Empty baseURL = Vite dev proxy; host-only env = Render blueprint (https added). */
export function apiBaseUrl(): string {
  const raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim() ?? '';
  if (!raw) return '';
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    return raw.replace(/\/$/, '');
  }
  return `https://${raw.replace(/\/$/, '')}`;
}

const client = axios.create({
  baseURL: apiBaseUrl(),
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

export default client;

export async function getScenarios() {
  const res = await client.get('/api/scenarios');
  return res.data.data;
}

export async function getDevices(scenarioId?: string) {
  const res = await client.get('/api/devices', {
    params: scenarioId ? { scenario_id: scenarioId } : undefined,
  });
  return res.data.data;
}

export async function getDevice(id: string) {
  const res = await client.get(`/api/devices/${id}`);
  return res.data.data;
}

export async function getDeviceHealth(id: string) {
  const res = await client.get(`/api/devices/${id}/health`);
  return res.data.data;
}

export async function getIncidents(scenarioId?: string) {
  const res = await client.get('/api/incidents', {
    params: scenarioId ? { scenario_id: scenarioId } : undefined,
  });
  return res.data.data;
}

export async function getIncident(id: string) {
  const res = await client.get(`/api/incidents/${id}`);
  return res.data.data;
}

export async function getIncidentTimeline(id: string) {
  const res = await client.get(`/api/incidents/${id}/timeline`);
  return res.data.data;
}

export async function getIncidentCorrelation(id: string) {
  const res = await client.get(`/api/incidents/${id}/correlation`);
  return res.data.data;
}

export async function getConfigDiff(deviceId: string, diffId: string) {
  const res = await client.get(`/api/devices/${deviceId}/config/diff/${diffId}`);
  return res.data.data;
}

export async function runSimulationStep(scenarioId: string) {
  const res = await client.post('/api/simulation/run-step', { auto_advance: true }, {
    params: { scenario_id: scenarioId },
  });
  return res.data.data;
}

export async function resetSimulation(scenarioId: string) {
  const res = await client.post('/api/simulation/reset', null, {
    params: { scenario_id: scenarioId },
  });
  return res.data.data;
}

export async function getSimulationStatus(scenarioId: string) {
  const res = await client.get('/api/simulation/status', {
    params: { scenario_id: scenarioId },
  });
  return res.data.data;
}
