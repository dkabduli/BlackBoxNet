import { Handle, Position, type NodeProps } from '@xyflow/react';
import {
  RouterIcon,
  SwitchIcon,
  FirewallIcon,
  UsersIcon,
  ServerIcon,
  CloudIcon,
  FECIcon,
} from './NetworkIcons';

export type NetworkNodeData = {
  label: string;
  ip?: string;
  role?: string;
  isRootCause?: boolean;
  health?: 'healthy' | 'degraded' | 'down';
  vendor?: 'cisco' | 'juniper' | 'nokia';
};

const roleToIcon = (role: string | undefined, isRootCause: boolean) => {
  const color = isRootCause ? '#f87171' : '#4ade80';
  switch (role) {
    case 'edge-router':
    case 'core-router':
    case 'pe-router':
    case 'p-router':
      return <RouterIcon size={48} color={color} />;
    case 'dist-switch':
    case 'access-switch':
    case 'rogue':
      return <SwitchIcon size={48} color={color} />;
    case 'firewall':
    case 'rr':
      return <FirewallIcon size={48} color={color} />;
    case 'users':
      return <UsersIcon size={48} color="#f87171" />;
    case 'fec':
      return <FECIcon size={48} color="#f87171" />;
    case 'cloud':
      return <CloudIcon size={48} color="#818cf8" />;
    default:
      return <RouterIcon size={48} color={color} />;
  }
};

const healthRingColor = {
  healthy: '#4ade80',
  degraded: '#fbbf24',
  down: '#f87171',
};

export default function NetworkNode({ data }: NodeProps) {
  const nodeData = data as NetworkNodeData;
  const { label, ip, role, isRootCause = false, health = 'healthy' } = nodeData;
  const ringColor = isRootCause ? '#f87171' : healthRingColor[health];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <Handle type="target" position={Position.Top} id="top" style={{ opacity: 0, width: 8, height: 8 }} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ opacity: 0, width: 8, height: 8 }} />
      <Handle type="target" position={Position.Left} id="left" style={{ opacity: 0, width: 8, height: 8 }} />
      <Handle type="source" position={Position.Right} id="right" style={{ opacity: 0, width: 8, height: 8 }} />

      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 14,
          background: 'rgba(15, 23, 42, 0.7)',
          border: `2.5px solid ${ringColor}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: isRootCause ? `0 0 16px ${ringColor}55` : 'none',
          transition: 'border-color 0.3s, box-shadow 0.3s',
        }}
      >
        {roleToIcon(role, isRootCause)}
      </div>

      <div style={{ textAlign: 'center', maxWidth: 100 }}>
        <div
          style={{
            color: isRootCause ? '#fca5a5' : '#f1f5f9',
            fontSize: 12,
            fontWeight: 600,
            lineHeight: 1.3,
            whiteSpace: 'nowrap',
          }}
        >
          {label}
        </div>
        {ip && <div style={{ color: '#64748b', fontSize: 10, marginTop: 1 }}>{ip}</div>}
        {isRootCause && (
          <div
            style={{
              color: '#f87171',
              fontSize: 9,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginTop: 2,
            }}
          >
            Root cause
          </div>
        )}
      </div>
    </div>
  );
}
