import { Server, Cpu, HardDrive, Timer, Wifi } from 'lucide-react';
import type { Device } from '../../types';
import { healthColor, healthBg, cn } from '../../lib/utils';

interface Props {
  device: Device;
  onClick?: () => void;
}

function MetricBar({ label, value, icon: Icon, unit, max = 100 }: {
  label: string; value?: number; icon: React.ElementType; unit: string; max?: number;
}) {
  const pct = value != null ? Math.min((value / max) * 100, 100) : 0;
  const barColor = pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="flex items-center gap-1 text-gray-400">
          <Icon className="w-3 h-3" />{label}
        </span>
        <span className="text-gray-300">{value != null ? `${value.toFixed(1)}${unit}` : 'N/A'}</span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function DeviceCard({ device, onClick }: Props) {
  const snap = device.latest_snapshot;
  const status = snap?.health_status || 'unknown';
  const isRealSsh = snap?.snapshot_source === 'ssh';

  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-xl border p-5 transition-all cursor-pointer hover:ring-1 hover:ring-blue-500/50 bg-gray-900/50',
        healthBg(status)
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gray-800">
            <Server className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{device.hostname}</h3>
            <p className="text-xs text-gray-400">{device.management_ip}</p>
          </div>
        </div>
        <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium uppercase', healthColor(status), healthBg(status))}>
          {status}
        </span>
      </div>

      <div className="flex gap-2 mb-4">
        <span className="px-2 py-0.5 rounded bg-gray-800 text-xs text-gray-300">{device.vendor}</span>
        <span className="px-2 py-0.5 rounded bg-gray-800 text-xs text-gray-300">{device.role}</span>
        {isRealSsh && (
          <span className="px-2 py-0.5 rounded bg-blue-500/20 text-xs text-blue-300">live ssh config</span>
        )}
      </div>

      <div className="space-y-2.5">
        <MetricBar label="CPU" value={snap?.cpu_usage ?? undefined} icon={Cpu} unit="%" />
        <MetricBar label="Memory" value={snap?.memory_usage ?? undefined} icon={HardDrive} unit="%" />
        <MetricBar label="Latency" value={snap?.latency_ms ?? undefined} icon={Timer} unit="ms" max={200} />
        <MetricBar label="Pkt Loss" value={snap?.packet_loss_pct ?? undefined} icon={Wifi} unit="%" />
      </div>
    </div>
  );
}
