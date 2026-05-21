import dagre from 'dagre';
import type { Node, Edge } from '@xyflow/react';
import type { Device, TopologySpec } from '../../types';
import type { NetworkNodeData } from './NetworkNode';
import type { NetworkEdgeData } from './NetworkEdgeLabel';

type LayoutMap = Record<string, { x: number; y: number }>;

function mapHealth(status?: string): 'healthy' | 'degraded' | 'down' {
  if (status === 'critical' || status === 'down') return 'down';
  if (status === 'degraded' || status === 'warning') return 'degraded';
  return 'healthy';
}

const guessRole = (deviceId: string): string => {
  if (deviceId.includes('edge')) return 'edge-router';
  if (deviceId.includes('core')) return 'core-router';
  if (deviceId.includes('dist')) return 'dist-switch';
  if (deviceId.includes('access')) return 'access-switch';
  if (deviceId.includes('rogue')) return 'rogue';
  if (deviceId.includes('srx')) return 'firewall';
  if (deviceId.includes('rr')) return 'rr';
  if (deviceId.includes('pe')) return 'pe-router';
  if (deviceId.includes('p-router') || deviceId === 'p-router') return 'p-router';
  if (deviceId === '_users' || deviceId === 'users') return 'users';
  if (deviceId === '_fec' || deviceId === 'fec' || deviceId === 'FEC' || deviceId === '_sdp') return 'fec';
  if (deviceId.startsWith('R') && deviceId.length <= 3) return 'edge-router';
  return 'edge-router';
};

function applyDagreLayout(nodes: Node[], edges: Edge[], direction = 'LR'): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, ranksep: 120, nodesep: 80 });

  nodes.forEach((n) => g.setNode(n.id, { width: 100, height: 100 }));
  edges.forEach((e) => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - 50, y: pos.y - 50 } };
  });
}

export function topologyToFlow(
  topology: TopologySpec | undefined,
  devices: Device[],
  rootCauseHostname?: string
): { nodes: Node[]; edges: Edge[] } {
  if (!topology?.links?.length) return { nodes: [], edges: [] };

  const { links, layout = 'linear', hub, annotations: _annotations } = topology;

  const deviceSet = new Set<string>();
  links.forEach((link) => {
    deviceSet.add(link.from);
    deviceSet.add(link.to);
  });
  const allDeviceIds = Array.from(deviceSet);

  const deviceMap: Record<string, Device> = {};
  devices.forEach((d) => {
    deviceMap[d.hostname] = d;
    deviceMap[d.id] = d;
  });

  let positions: LayoutMap = {};

  if (layout === 'linear') {
    const nonTerminal = allDeviceIds.filter(
      (id) => !links.find((l) => l.to === id && l.terminal)
    );
    const terminals = allDeviceIds.filter((id) =>
      links.find((l) => l.to === id && l.terminal)
    );
    [...nonTerminal, ...terminals].forEach((id, i) => {
      positions[id] = { x: 80 + i * 260, y: 220 };
    });
  } else if (layout === 'ospf-areas') {
    positions['R1'] = { x: 80, y: 100 };
    positions['R2'] = { x: 600, y: 100 };
    positions['R3'] = { x: 80, y: 380 };
    positions['R4'] = { x: 600, y: 380 };
  } else if (layout === 'junos-triangle') {
    const place: LayoutMap = {
      'edge-router': { x: 420, y: 40 },
      'rr-1': { x: 100, y: 400 },
      'pe-1': { x: 740, y: 400 },
      'ce-1': { x: 80, y: 200 },
      'p-1': { x: 420, y: 220 },
      'ingress-pe': { x: 120, y: 380 },
      'transit-p': { x: 420, y: 80 },
      'egress-pe': { x: 740, y: 380 },
    };
    allDeviceIds.forEach((id) => {
      if (place[id]) positions[id] = place[id];
    });
    const unset = allDeviceIds.filter((id) => !positions[id] && !id.startsWith('_'));
    unset.forEach((id, i) => {
      positions[id] = { x: 200 + i * 280, y: 200 + (i % 2) * 180 };
    });
    const terminals = allDeviceIds.filter((id) => id === '_users' || id === '_fec');
    terminals.forEach((id, i) => {
      positions[id] = { x: 360 + i * 140, y: 520 };
    });
  } else if (layout === 'triangle') {
    const ids = allDeviceIds.filter((id) => id !== '_users' && id !== '_fec');
    if (ids[0]) positions[ids[0]] = { x: 340, y: 60 };
    if (ids[1]) positions[ids[1]] = { x: 100, y: 360 };
    if (ids[2]) positions[ids[2]] = { x: 580, y: 360 };
  } else if (layout === 'nokia-hub') {
    const hubId = hub ?? 'p-router';
    positions[hubId] = { x: 400, y: 160 };
    const spokes = allDeviceIds.filter(
      (id) => id !== hubId && id !== '_users' && id !== '_fec' && !id.startsWith('_')
    );
    const spokeSlots: LayoutMap = {
      'pe-1': { x: 120, y: 360 },
      'pe-2': { x: 680, y: 360 },
      'pe-agg': { x: 120, y: 380 },
      'pe-access': { x: 680, y: 380 },
    };
    spokes.forEach((id, i) => {
      positions[id] = spokeSlots[id] ?? {
        x: 400 + (i === 0 ? -280 : 280),
        y: 360,
      };
    });
    const terminals = allDeviceIds.filter((id) => id === '_users' || id === '_fec' || id === '_sdp');
    terminals.forEach((id, i) => {
      positions[id] = { x: 320 + i * 160, y: 520 };
    });
  } else if (layout === 'hub' || layout === 'star') {
    const hubId = hub ?? allDeviceIds[0];
    positions[hubId] = { x: 340, y: 200 };
    const spokes = allDeviceIds.filter(
      (id) => id !== hubId && id !== '_users' && id !== '_fec'
    );
    const terminals = allDeviceIds.filter((id) => id === '_users' || id === '_fec');
    spokes.forEach((id, i) => {
      const angle = (i / spokes.length) * Math.PI * 2 - Math.PI / 2;
      positions[id] = {
        x: 340 + Math.cos(angle) * 220,
        y: 200 + Math.sin(angle) * 180,
      };
    });
    terminals.forEach((id, i) => {
      positions[id] = { x: 280 + i * 120, y: 440 };
    });
  } else {
    allDeviceIds.forEach((id, i) => {
      positions[id] = { x: 80 + i * 240, y: 200 };
    });
  }

  let nodes: Node<NetworkNodeData>[] = allDeviceIds.map((id) => {
    const apiDevice = deviceMap[id];
    const isTerminal = !!links.find((l) => l.to === id && l.terminal);
    const terminalRole =
      id.includes('fec') || id.includes('FEC') ? 'fec' : id === '_users' ? 'users' : undefined;

    return {
      id,
      type: 'networkNode',
      position: positions[id] ?? { x: 0, y: 0 },
      data: {
        label: apiDevice?.hostname ?? id.replace(/^_/, ''),
        ip: apiDevice?.management_ip,
        role: isTerminal ? terminalRole : (apiDevice?.role ?? guessRole(id)),
        isRootCause: !!rootCauseHostname && id === rootCauseHostname,
        health: apiDevice ? mapHealth(apiDevice.latest_snapshot?.health_status) : 'healthy',
        vendor: apiDevice?.vendor as NetworkNodeData['vendor'],
      },
    };
  });

  const edges: Edge<NetworkEdgeData>[] = links.map((link, i) => {
    const isRogue = link.type === 'rogue-uplink';
    return {
      id: `edge-${i}`,
      source: link.from,
      target: link.to,
      type: 'networkEdge',
      data: {
        leftPort: link.left_port,
        rightPort: link.right_port,
        subnet: link.subnet,
        linkType: link.type,
      },
      animated:
        link.type === 'ldp' || link.type === 'ibgp' || link.type === 'ebgp',
      style: { stroke: isRogue ? '#f87171' : undefined },
    };
  });

  if (layout === 'linear' || layout === 'ospf-areas') {
    const dir = layout === 'linear' ? 'LR' : 'TB';
    nodes = applyDagreLayout(nodes, edges, dir) as Node<NetworkNodeData>[];
  }

  return { nodes, edges };
}
