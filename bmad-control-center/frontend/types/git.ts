export type GitFileCategory = 'staged' | 'unstaged' | 'untracked' | 'conflict'

export interface GitFileEntry {
  relative_path: string
  category: GitFileCategory
  status_code: string
  lines_added?: number
  lines_deleted?: number
  is_binary?: boolean
  size_bytes?: number
}

export interface GitWorkingTree {
  staged: GitFileEntry[]
  unstaged: GitFileEntry[]
  untracked: GitFileEntry[]
  conflicts: GitFileEntry[]
}

export interface GitStatusResponse {
  current_branch: string
  head_commit_hash: string
  head_commit_short: string
  head_commit_message: string
  head_commit_author: string
  head_committed_at: string
  upstream_branch?: string | null
  is_detached: boolean
  is_conflicted: boolean
  is_syncing: boolean
  staged_count: number
  unstaged_count: number
  untracked_count: number
  total_modified_files: number
  working_tree: GitWorkingTree
  captured_at_utc: string
}

export interface GitCommitFileChange {
  relative_path: string
  change_type: 'added' | 'modified' | 'deleted' | 'renamed' | string
  is_binary: boolean
  is_diff_omitted: boolean
  insertions: number
  deletions: number
  size_bytes?: number
}

export interface GitCommitItem {
  commit_hash: string
  short_hash: string
  author_name: string
  author_email: string
  committed_at: string
  message: string
  agent_role?: string
  files_changed_count: number
  insertions: number
  deletions: number
  files?: GitCommitFileChange[]
}

export interface GitCommitListResponse {
  commits: GitCommitItem[]
  total_count: number
  limit: number
  offset: number
  has_more: boolean
  execution_time_ms?: number
}

export interface GitBranchItem {
  name: string
  target_commit_hash: string
  short_hash: string
  is_current: boolean
  is_remote_tracking: boolean
  upstream_branch?: string | null
}

export interface GitBranchListResponse {
  current_branch: string
  total_branches: number
  branches: GitBranchItem[]
}

export interface GitErrorResponse {
  error_code: string
  detail: string
  status_code: number
  path?: string
}
