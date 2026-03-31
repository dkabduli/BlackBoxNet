import { Router, Server, ShieldCheck } from 'lucide-react';
import type { Device } from '../../types';
import { cn, healthColor } from '../../lib/utils';

interface Props {
  devices: Device[];
  highlightedDeviceId?: string;
}

const roleOrder = ['edge-router', 'dist-switch', 'access-switch'];

function roleLabel(role: string) {
  if (role === 'edge-router') return 'Edge Router';
  if (role === 'dist-switch') return 'Distribution Switch';
  if (role === 'access-switch') return 'Access Switch';
  return role;
}

function roleIcon(role: string) {
  if (role === 'edge-router') return Router;
  if (role === 'dist-switch') return ShieldCheck;
  return Server;
}

function DeviceNode({
  device,
  highlighted,
}: {
  device: Device;
  highlighted?: boolean;
}) {
  const status = device.latest_snapshot?.health_status ?? 'unknown';
  const Icon = roleIcon(device.role);

  return (
    <div className="flex w-32 flex-col items-center text-center">
      <div
        className={cn(
          'flex h-14 w-14 items-center justify-center rounded-xl border bg-slate-800/90 shadow-sm',
          highlighted ? 'border-red-400 ring-2 ring-red-400/40' : 'border-slate-700'
        )}
      >
        <Icon className={cn('h-7 w-7', healthColor(status), status === 'unknown' && 'text-blue-400')} />
      </div>
      <p className="mt-2 text-xs font-semibold text-white">{device.hostname}</p>
      <p className="text-[11px] text-gray-400">{roleLabel(device.role)}</p>
      <div className="mt-1 text-[10px] leading-4 text-gray-500">
        <p>{device.management_ip}</p>
        {highlighted && <p className="text-red-300">Root cause suspect</p>}
      </div>
    </div>
  );
}

function LinkLabel({
  leftPort,
  rightPort,
  subnet,
}: {
  leftPort: string;
  rightPort: string;
  subnet: string;
}) {
  return (
    <div className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 text-center text-[10px] text-cyan-200">
      <p>{leftPort} <span className="text-cyan-400">to</span> {rightPort}</p>
      <p className="text-cyan-300/80">{subnet}</p>
    </div>
  );
}

export default function TopologyPreview({ devices, highlightedDeviceId }: Props) {
  const orderedDevices = [...devices].sort((a, b) => {
    const aIndex = roleOrder.indexOf(a.role);
    const bIndex = roleOrder.indexOf(b.role);
    return (aIndex === -1 ? Number.MAX_SAFE_INTEGER : aIndex) - (bIndex === -1 ? Number.MAX_SAFE_INTEGER : bIndex);
  });

  const edge = orderedDevices.find((device) => device.role === 'edge-router');
  const dist = orderedDevices.find((device) => device.role === 'dist-switch');
  const access = orderedDevices.find((device) => device.role === 'access-switch');

  if (!edge || !dist || !access) {
    return null;
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white">Topology Preview</h3>
          <p className="text-xs text-gray-400">Compact demo network diagram with ports and addressing</p>
        </div>
        <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs text-blue-300">
          Impacted subnet: 10.0.1.0/24
        </span>
      </div>

      <div className="hidden lg:block">
        <div className="grid grid-cols-[auto_1fr_auto_1fr_auto] items-start gap-3 overflow-x-auto pb-1">
          <div className="pt-4">
            <DeviceNode device={edge} highlighted={edge.id === highlightedDeviceId} />
          </div>

          <div className="flex min-w-44 flex-col items-center gap-1 pt-11">
            <div className={cn('h-px w-full', highlightedDeviceId === edge.id ? 'bg-red-400' : 'bg-slate-500')} />
            <LinkLabel leftPort="Gi0/0" rightPort="Gi0/1" subnet="10.0.0.0/24 transit" />
          </div>

          <div className="pt-4">
            <DeviceNode device={dist} highlighted={dist.id === highlightedDeviceId} />
          </div>

          <div className="flex min-w-44 flex-col items-center gap-1 pt-11">
            <div className={cn('h-px w-full', highlightedDeviceId ? 'bg-red-400/70' : 'bg-slate-500')} />
            <LinkLabel leftPort="Gi0/2" rightPort="Gi0/1" subnet="802.1Q trunk" />
          </div>

          <div className="pt-4">
            <DeviceNode device={access} highlighted={access.id === highlightedDeviceId} />
            <div className="mt-2 rounded-md border border-red-500/20 bg-red-500/10 px-2 py-1 text-center text-[10px] text-red-200">
              <p>Gi0/24 to users</p>
              <p className="text-red-300/80">10.0.1.0/24</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-2 lg:hidden">
        <DeviceNode device={edge} highlighted={edge.id === highlightedDeviceId} />
        <LinkLabel leftPort="Gi0/0" rightPort="Gi0/1" subnet="10.0.0.0/24 transit" />
        <DeviceNode device={dist} highlighted={dist.id === highlightedDeviceId} />
        <LinkLabel leftPort="Gi0/2" rightPort="Gi0/1" subnet="802.1Q trunk" />
        <DeviceNode device={access} highlighted={access.id === highlightedDeviceId} />
        <div className="rounded-md border border-red-500/20 bg-red-500/10 px-2 py-1 text-[10px] text-red-200">
          Gi0/24 to users on 10.0.1.0/24
        </div>
      </div>
    </div>
  );
}
