import {
  type EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from '@xyflow/react';

export type NetworkEdgeData = {
  leftPort?: string;
  rightPort?: string;
  subnet?: string;
  linkType?: string;
};

const linkStyle = (
  type: string | undefined
): { stroke: string; strokeDasharray?: string; strokeWidth: number } => {
  switch (type) {
    case 'routed':
      return { stroke: '#4ade80', strokeWidth: 2 };
    case 'trunk':
      return { stroke: '#60a5fa', strokeWidth: 2.5 };
    case 'serial':
      return { stroke: '#a78bfa', strokeWidth: 2, strokeDasharray: '6 3' };
    case 'ldp':
      return { stroke: '#f59e0b', strokeWidth: 2, strokeDasharray: '4 2' };
    case 'ibgp':
      return { stroke: '#34d399', strokeWidth: 1.5, strokeDasharray: '8 4' };
    case 'ebgp':
      return { stroke: '#f97316', strokeWidth: 2 };
    case 'ospf-backbone':
      return { stroke: '#818cf8', strokeWidth: 2.5 };
    case 'rogue-uplink':
      return { stroke: '#f87171', strokeWidth: 2, strokeDasharray: '5 3' };
    case 'mpls-fec':
      return { stroke: '#f87171', strokeWidth: 1.5, strokeDasharray: '4 2' };
    case 'service':
    case 'access':
      return { stroke: '#22d3ee', strokeWidth: 1.5 };
    default:
      return { stroke: '#64748b', strokeWidth: 1.5 };
  }
};

const linkTypeLabel = (type: string | undefined) => {
  if (!type) return null;
  const map: Record<string, string> = {
    routed: 'ROUTED',
    trunk: 'TRUNK',
    serial: 'SERIAL',
    ldp: 'LDP',
    ibgp: 'iBGP',
    ebgp: 'eBGP',
    'ospf-backbone': 'OSPF',
    'rogue-uplink': 'ROGUE',
    'mpls-fec': 'MPLS-FEC',
    service: 'SERVICE',
    access: 'ACCESS',
  };
  return map[type] ?? type.toUpperCase();
};

export default function NetworkEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data = {},
}: EdgeProps) {
  const edgeData = (data ?? {}) as NetworkEdgeData;
  const { leftPort, rightPort, subnet, linkType } = edgeData;
  const style = linkStyle(linkType);

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const srcLabelX = sourceX + (labelX - sourceX) * 0.4;
  const srcLabelY = sourceY + (labelY - sourceY) * 0.4;
  const tgtLabelX = targetX + (labelX - targetX) * 0.4;
  const tgtLabelY = targetY + (labelY - targetY) * 0.4;

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
          }}
          className="nodrag nopan"
        >
          {subnet && (
            <div
              style={{
                background: 'rgba(15,23,42,0.85)',
                border: `1px solid ${style.stroke}44`,
                borderRadius: 5,
                padding: '2px 7px',
                color: style.stroke,
                fontSize: 10,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {subnet}
            </div>
          )}
          {linkType && (
            <div
              style={{
                background: `${style.stroke}22`,
                border: `1px solid ${style.stroke}55`,
                borderRadius: 4,
                padding: '1px 5px',
                color: style.stroke,
                fontSize: 9,
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              {linkTypeLabel(linkType)}
            </div>
          )}
        </div>

        {leftPort && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${srcLabelX}px,${srcLabelY}px)`,
              background: 'rgba(15,23,42,0.75)',
              border: '1px solid #334155',
              borderRadius: 4,
              padding: '1px 5px',
              color: '#94a3b8',
              fontSize: 9,
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
            }}
            className="nodrag nopan"
          >
            {leftPort}
          </div>
        )}

        {rightPort && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${tgtLabelX}px,${tgtLabelY}px)`,
              background: 'rgba(15,23,42,0.75)',
              border: '1px solid #334155',
              borderRadius: 4,
              padding: '1px 5px',
              color: '#94a3b8',
              fontSize: 9,
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
            }}
            className="nodrag nopan"
          >
            {rightPort}
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
}
