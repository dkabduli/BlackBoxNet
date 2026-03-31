import axios from 'axios';

const client = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

export default client;

export async function getDevices() {
  const res = await client.get('/api/devices');
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

export async function getIncidents() {
  const res = await client.get('/api/incidents');
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

export async function runSimulationStep() {
  const res = await client.post('/api/simulation/run-step', { auto_advance: true });
  return res.data.data;
}

export async function resetSimulation() {
  const res = await client.post('/api/simulation/reset');
  return res.data.data;
}

export async function getSimulationStatus() {
  const res = await client.get('/api/simulation/status');
  return res.data.data;
}
