import { useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  type NodeTypes,
  type EdgeTypes,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import type { Device, TopologySpec } from '../../types';
import { useScenario } from '../../context/ScenarioContext';
import NetworkNode from './NetworkNode';
import NetworkEdge from './NetworkEdgeLabel';
import { topologyToFlow } from './topologyToFlow';

const nodeTypes: NodeTypes = { networkNode: NetworkNode };
const edgeTypes: EdgeTypes = { networkEdge: NetworkEdge };

interface TopologyPreviewProps {
  devices: Device[];
  topology?: TopologySpec;
  topologyType?: string;
  affectedSubnet?: string;
  highlightedDeviceId?: string;
  highlightedHostname?: string;
  rootCauseDeviceId?: string;
  layoutLabel?: string;
  annotations?: string[];
  /** True when diagram is from scenario spec only (no simulation run yet). */
  previewBeforeSimulation?: boolean;
}

export default function TopologyPreview({
  devices,
  topology: topologyProp,
  topologyType = 'linear',
  affectedSubnet: affectedSubnetProp,
  highlightedDeviceId,
  highlightedHostname,
  rootCauseDeviceId,
  layoutLabel: layoutLabelProp,
  annotations: annotationsProp,
  previewBeforeSimulation = false,
}: TopologyPreviewProps) {
  const { activeScenario } = useScenario();
  const topology = topologyProp ?? activeScenario?.topology;
  const layout = topology?.layout ?? topologyType;
  const affectedSubnet = topology?.affected_subnet ?? affectedSubnetProp ?? activeScenario?.affected_subnet;
  const layoutLabel = layoutLabelProp ?? layout;

  const rootCauseHostname =
    highlightedHostname ??
    (rootCauseDeviceId
      ? devices.find((d) => d.id === rootCauseDeviceId)?.hostname
      : undefined) ??
    (highlightedDeviceId
      ? devices.find((d) => d.id === highlightedDeviceId)?.hostname
      : undefined);

  const annotationTexts = useMemo(() => {
    if (annotationsProp?.length) return annotationsProp;
    const raw = topology?.annotations;
    if (!raw?.length) return [];
    return raw.map((a) => (typeof a === 'string' ? a : a.text));
  }, [annotationsProp, topology?.annotations]);

  const resolvedRootCauseDeviceId = rootCauseDeviceId ?? highlightedDeviceId;

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => topologyToFlow(topology, devices, rootCauseHostname, resolvedRootCauseDeviceId),
    [topology, devices, rootCauseHostname, resolvedRootCauseDeviceId]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  if (!topology?.links?.length) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 text-sm text-gray-500">
        Topology spec missing — run scenario generator.
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: 520,
        borderRadius: 12,
        overflow: 'hidden',
        background: '#0d1117',
        border: '1px solid #1f2937',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(13,17,23,0.85)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid #1e293b',
        }}
      >
        <div>
          <span style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>Topology Preview</span>
          {layoutLabel && (
            <span style={{ color: '#64748b', fontSize: 12, marginLeft: 10 }}>
              {layoutLabel.charAt(0).toUpperCase() + layoutLabel.slice(1).replace(/-/g, ' ')}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {previewBeforeSimulation && (
            <span
              style={{
                background: 'rgba(34,197,94,0.12)',
                border: '1px solid rgba(34,197,94,0.4)',
                borderRadius: 20,
                padding: '3px 10px',
                color: '#86efac',
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              Preview — run T1 to simulate
            </span>
          )}
          {affectedSubnet && (
            <div
              style={{
                background: 'rgba(59,130,246,0.15)',
                border: '1px solid rgba(59,130,246,0.5)',
                borderRadius: 20,
                padding: '3px 12px',
                color: '#93c5fd',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              Impacted: {affectedSubnet}
            </div>
          )}
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.3}
        maxZoom={2}
        style={{ background: '#0d1117' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1} color="#1e293b" />
        <Controls
          style={{
            background: '#0d1117',
            border: '1px solid #1e293b',
            borderRadius: 8,
          }}
        />
      </ReactFlow>

      {annotationTexts.length > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'rgba(13,17,23,0.9)',
            backdropFilter: 'blur(8px)',
            borderTop: '1px solid #1e293b',
            padding: '6px 16px',
            display: 'flex',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          {annotationTexts.map((note, i) => (
            <span key={i} style={{ color: '#94a3b8', fontSize: 11 }}>
              {note}
            </span>
          ))}
        </div>
      )}

      <Legend />
    </div>
  );
}

function Legend() {
  const items = [
    { color: '#4ade80', label: 'Routed', dash: false },
    { color: '#60a5fa', label: 'Trunk', dash: false },
    { color: '#a78bfa', label: 'Serial', dash: true },
    { color: '#f59e0b', label: 'LDP', dash: true },
    { color: '#34d399', label: 'iBGP', dash: true },
    { color: '#f97316', label: 'eBGP', dash: false },
    { color: '#818cf8', label: 'OSPF', dash: false },
    { color: '#f87171', label: 'Rogue', dash: true },
  ];
  return (
    <div
      style={{
        position: 'absolute',
        top: 52,
        right: 10,
        zIndex: 10,
        background: 'rgba(13,17,23,0.92)',
        backdropFilter: 'blur(6px)',
        border: '1px solid #1e293b',
        borderRadius: 8,
        padding: '6px 10px',
        display: 'grid',
        gridTemplateColumns: 'repeat(2, auto)',
        columnGap: 14,
        rowGap: 3,
        pointerEvents: 'none',
      }}
    >
      <span style={{ color: '#64748b', fontSize: 9, fontWeight: 700, gridColumn: '1 / -1', marginBottom: 2 }}>
        LINK TYPES
      </span>
      {items.map(({ color, label, dash }) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <svg width="22" height="6">
            <line
              x1="0"
              y1="3"
              x2="22"
              y2="3"
              stroke={color}
              strokeWidth="2"
              strokeDasharray={dash ? '4 3' : undefined}
            />
          </svg>
          <span style={{ color: '#94a3b8', fontSize: 9 }}>{label}</span>
        </div>
      ))}
    </div>
  );
}
