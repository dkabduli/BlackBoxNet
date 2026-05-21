export interface InterfaceSnapshot {
  name: string;
  admin_state: string;
  oper_state: string;
  rx_errors: number;
  tx_errors: number;
  description?: string;
  ip_address?: string;
  speed_mbps?: number;
}

export interface LatestSnapshot {
  id?: string;
  timestamp?: string;
  config_hash?: string;
  snapshot_source: string;
  cpu_usage?: number;
  memory_usage?: number;
  latency_ms?: number;
  packet_loss_pct?: number;
  health_status: string;
  interfaces: InterfaceSnapshot[];
  tags: string[];
}

export interface Device {
  id: string;
  hostname: string;
  management_ip: string;
  vendor: string;
  role: string;
  latest_snapshot?: LatestSnapshot;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface TopologyLink {
  from: string;
  to: string;
  left_port?: string;
  right_port?: string;
  subnet?: string;
  type?: string;
  area?: string;
  terminal?: boolean;
}

export interface TopologySpec {
  layout: string;
  affected_subnet?: string;
  hub?: string;
  links: TopologyLink[];
  annotations?: { id: string; text: string }[];
}

export interface ScenarioCatalogItem {
  id: string;
  label: string;
  name: string;
  description: string;
  vendor: string;
  vendor_group?: string;
  vendor_cli?: string;
  tab_order: number;
  topology_type: string;
  topology?: TopologySpec;
  device_count: number;
  affected_subnet?: string;
  demo_path?: string;
  step_labels?: Record<string, string>;
}

export interface Incident {
  id: string;
  scenario_id?: string;
  title: string;
  start_time: string;
  end_time?: string;
  status: string;
  affected_scope?: string;
  root_device?: { id: string; hostname: string; vendor?: string; role?: string };
  summary?: string;
  suspicion_summary?: string;
  event_count: number;
  affected_device_count: number;
  affected_devices?: AffectedDevice[];
  event_summary?: { total: number; by_type: Record<string, number> };
  created_at: string;
}

export interface AffectedDevice {
  device_id: string;
  hostname: string;
  impact_level: string;
}

export interface TimelineEvent {
  id: string;
  device_id: string;
  device_hostname: string;
  timestamp: string;
  event_type: string;
  severity: string;
  title: string;
  description?: string;
  config_diff?: { diff_id: string; summary: string; suspicion_level: string };
  is_primary_cause: boolean;
  relevance_score: number;
  metadata: Record<string, unknown>;
}

export interface ConfigDiff {
  id: string;
  device_id: string;
  device_hostname?: string;
  timestamp: string;
  previous_version?: { id: string; timestamp: string; git_commit_hash: string };
  current_version?: { id: string; timestamp: string; git_commit_hash: string };
  diff_text: string;
  lines_added: number;
  lines_removed: number;
  lines_changed: number;
  semantic_summary: SemanticChange[];
  suspicion_level: string;
  summary?: string;
  config_source?: string;
  redacted?: boolean;
}

export interface SemanticChange {
  change_type: string;
  entity: string;
  action: string;
  details: Record<string, unknown>;
  suspicion_level: string;
  reason: string;
}

export interface CorrelationData {
  incident_id: string;
  suspicion_summary?: string;
  primary_suspect?: {
    event_id: string;
    event_type: string;
    device_id: string;
    timestamp: string;
  };
  correlation_flags: CorrelationFlag[];
  recommendation?: string;
}

export interface CorrelationFlag {
  rule: string;
  suspicion_level: string;
  description: string;
  evidence: Record<string, unknown>;
}

export interface SimulationStatus {
  current_time: number;
  current_step: string;
  current_step_description?: string;
  total_steps: number;
  scenario_name: string;
  scenario_id: string;
  scenario_label?: string;
  vendor?: string;
  topology_type?: string;
  demo_path?: string;
  affected_subnet?: string;
  step_labels?: Record<string, string>;
  devices: { device_id: string; hostname: string; vendor?: string; current_state: string }[];
  progress: {
    percentage: number;
    next_step?: string;
    can_advance: boolean;
    can_run_current_step: boolean;
    has_current_step_data: boolean;
    is_complete: boolean;
  };
}

export interface RunStepResult {
  current_time: number;
  time_step: string;
  devices_collected: number;
  snapshots_created: number;
  events_generated: { event_id: string; event_type: string; device_id: string; severity: string; title: string }[];
  incidents_created: number;
  git_commits: number;
}
