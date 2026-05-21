import '@xyflow/react/dist/style.css';
import { useMemo, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
  type OnNodesChange,
  type OnEdgesChange,
  type ReactFlowInstance,
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
  scenarioDescription?: string;
}

function fitPaddingForLayout(layout: string): number {
  if (layout === 'linear' || layout === 'ospf-areas') return 0.52;
  if (layout === 'nokia-hub' || layout === 'junos-triangle' || layout === 'hub' || layout === 'star') {
    return 0.48;
  }
  if (layout === 'triangle') return 0.45;
  return 0.4;
}

function TopologyFlowCanvas({
  layout,
  layoutLabel,
  affectedSubnet,
  previewBeforeSimulation,
  scenarioDescription,
  annotationTexts,
  rootCauseHostname,
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  nodeTypes,
  edgeTypes,
}: {
  layout: string;
  layoutLabel: string;
  affectedSubnet?: string;
  previewBeforeSimulation: boolean;
  scenarioDescription?: string;
  annotationTexts: string[];
  rootCauseHostname?: string;
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  nodeTypes: NodeTypes;
  edgeTypes: EdgeTypes;
}) {
  const fitPadding = fitPaddingForLayout(layout);
  const { fitView } = useReactFlow();

  const applyFit = useCallback(
    (instance?: ReactFlowInstance) => {
      const fn = instance?.fitView ?? fitView;
      requestAnimationFrame(() => {
        fn({ padding: fitPadding, duration: 150, maxZoom: 1.15 });
      });
    },
    [fitView, fitPadding]
  );

  useEffect(() => {
    applyFit();
  }, [nodes, edges, applyFit, layout]);

  return (
    <>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 12,
          background: 'rgba(13,17,23,0.85)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid #1e293b',
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>Topology Preview</span>
            {layoutLabel && (
              <span style={{ color: '#64748b', fontSize: 12 }}>
                {layoutLabel.charAt(0).toUpperCase() + layoutLabel.slice(1).replace(/-/g, ' ')}
              </span>
            )}
          </div>
          {scenarioDescription && (
            <p style={{ color: '#94a3b8', fontSize: 12, marginTop: 4, lineHeight: 1.4, maxWidth: 520 }}>
              {scenarioDescription}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', flexShrink: 0 }}>
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

      <p className="sr-only">
        Network topology diagram, {layoutLabel} layout, {nodes.length} devices, {edges.length} links.
        {rootCauseHostname ? ` Root cause: ${rootCauseHostname}.` : ''}
      </p>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onInit={applyFit}
        aria-label={`Network topology, ${layoutLabel} layout`}
        fitView
        fitViewOptions={{ padding: fitPadding, maxZoom: 1.15 }}
        minZoom={0.25}
        maxZoom={2}
        style={{ background: '#0d1117' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1} color="#1e293b" />
        <Controls
          position="bottom-right"
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
    </>
  );
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
  scenarioDescription: scenarioDescriptionProp,
}: TopologyPreviewProps) {
  const { activeScenario } = useScenario();
  const topology = topologyProp ?? activeScenario?.topology;
  const layout = topology?.layout ?? topologyType;
  const affectedSubnet = topology?.affected_subnet ?? affectedSubnetProp ?? activeScenario?.affected_subnet;
  const layoutLabel = layoutLabelProp ?? layout;
  const scenarioDescription =
    scenarioDescriptionProp ?? activeScenario?.description ?? undefined;

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
      <ReactFlowProvider>
        <TopologyFlowCanvas
          layout={layout}
          layoutLabel={layoutLabel}
          affectedSubnet={affectedSubnet}
          previewBeforeSimulation={previewBeforeSimulation}
          scenarioDescription={scenarioDescription}
          annotationTexts={annotationTexts}
          rootCauseHostname={rootCauseHostname}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
        />
      </ReactFlowProvider>
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
        left: 10,
        zIndex: 10,
        maxWidth: 200,
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
