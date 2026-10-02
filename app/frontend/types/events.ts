import type { WorkflowStatusResponse } from './workflow'

export type WebSocketEventType =
  | 'WORKFLOW_UPDATED'
  | 'ARTIFACT_TREE_CHANGED'
  | 'ARTIFACT_CHANGED'
  | 'GATE_STATE_CHANGED'
  | 'PING'
  | 'PONG'
  | 'HEARTBEAT_PING'
  | 'HEARTBEAT_PONG'
  | 'SYSTEM_NOTICE'
  | 'SUBSCRIBE_ARTIFACT'
  | 'GIT_STATUS_CHANGED'

export interface FileMetadataRecord {
  relative_path: string
  filename: string
  size_bytes: number
  mime_type?: string
  is_large_file?: boolean
  metadata_only?: boolean
  updated_at?: string
}

export interface WorkflowUpdatedPayload {
  active_stage: string
  overall_status?: string
  active_agent_role?: string | null
  agent_role?: string | null
  action_type?: string
  origin_block_index?: number
  handoff_target?: string
  last_artifact_path?: string
  last_open_points?: string
  has_pulse?: boolean
  active_artifact_in_progress?: string | null
  last_updated?: string
  completed_stages?: number
  total_stages?: number
  stages?: WorkflowStatusResponse['stages']
}

export interface ArtifactChangedPayload {
  change_type: 'created' | 'modified' | 'deleted' | string
  relative_path: string
  is_new_tag?: boolean
  size_bytes?: number
  file_metadata?: FileMetadataRecord
}

export interface SystemNoticePayload {
  notice_code: string
  message: string
  absorbed_mutations_count?: number
  window_duration_ms?: number
  coalesced_resource?: string
}

export interface GitStatusEventPayload {
  current_branch: string
  head_hash_short: string
  head_commit_message?: string
  head_commit_author?: string
  is_detached: boolean
  is_conflicted: boolean
  is_syncing: boolean
  staged_count: number
  unstaged_count: number
  untracked_count: number
  total_modified_files: number
  trigger_source?: string
  sync_latency_ms?: number
}

export interface WebSocketMessage<T = unknown> {
  event?: WebSocketEventType | string
  event_type?: WebSocketEventType | string
  event_id?: string
  resource_path?: string
  timestamp?: string
  coalesced_count?: number
  reception_latency_ms?: number
  data?: T
  payload?: T
  gate_id?: string
  action?: string
}

export interface PerimeterStatusResponse {
  sandbox_status: string
  zero_leakage_verified: boolean
  monitored_roots: Array<{ allowed_path: string; is_monitored: boolean }>
  ignored_external_events_count: number
  debounce_window_ms: number
  large_file_threshold_bytes: number
}
