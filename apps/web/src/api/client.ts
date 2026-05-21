import axios from 'axios';

/** Empty baseURL = Vite dev proxy; host-only env = Render blueprint (https added). */
export function apiBaseUrl(): string {
  const raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim() ?? '';
  if (raw) {
    if (raw.startsWith('http://') || raw.startsWith('https://')) {
      return raw.replace(/\/$/, '');
    }
    return `https://${raw.replace(/\/$/, '')}`;
  }
  // Static site may build before Render injects fromService; infer API host on Render.
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host.endsWith('.onrender.com') && host.includes('-web')) {
      return `https://${host.replace('-web', '-api')}`;
    }
  }
  return '';
}

const client = axios.create({
  baseURL: apiBaseUrl(),
  timeout: 120000,
});

const jsonPost = { headers: { 'Content-Type': 'application/json' } as const };

/** User-visible message from axios failures (cold start, CORS, 502, etc.). */
export function apiErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const ax = err as { response?: { status?: number; data?: { detail?: string } } };
    const detail = ax.response?.data?.detail;
    if (typeof detail === 'string' && detail) {
      return `${fallback} (${ax.response?.status ?? '?'}: ${detail})`;
    }
    if (ax.response?.status) return `${fallback} (HTTP ${ax.response.status})`;
  }
  if (err instanceof Error && err.message) return `${fallback}: ${err.message}`;
  return fallback;
}

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
  const res = await client.post(
    '/api/simulation/run-step',
    { auto_advance: true },
    { params: { scenario_id: scenarioId }, ...jsonPost }
  );
  return res.data.data;
}

export async function resetSimulation(scenarioId: string) {
  const res = await client.post(
    '/api/simulation/reset',
    {},
    { params: { scenario_id: scenarioId }, ...jsonPost }
  );
  return res.data.data;
}

export async function getSimulationStatus(scenarioId: string) {
  const res = await client.get('/api/simulation/status', {
    params: { scenario_id: scenarioId },
  });
  return res.data.data;
}
