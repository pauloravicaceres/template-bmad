export type NodeType = 'DIRECTORY' | 'FILE'

export interface DirectoryNode {
  node_id: string
  name: string
  node_type: NodeType
  relative_path: string
  parent_path: string | null
  child_file_count: number
  is_empty: boolean
  last_modified: string
  children?: DirectoryNode[]
}

export interface ArtifactTreeResponse {
  root_node: DirectoryNode
}

export interface ArtifactContent {
  relative_path: string
  filename: string
  raw_content: string | null
  detected_format: 'MARKDOWN' | 'TEXT' | 'UNSUPPORTED'
  encoding: string
  size_bytes: number
  is_oversized: boolean
  is_unsupported_media: boolean
  mime_type: string | null
  last_modified: string
}

export interface ApiErrorResponse {
  error_code:
    | 'PATH_TRAVERSAL_DETECTED'
    | 'ARTIFACT_NOT_FOUND'
    | 'PAYLOAD_TOO_LARGE'
    | 'UNSUPPORTED_MEDIA_TYPE'
    | 'INVALID_PARAMETER'
    | 'FILE_READ_ERROR'
    | 'DIRECTORY_SCAN_ERROR'
    | string
  detail: string
  timestamp: string
  path: string
  metadata?: {
    filename?: string
    size_bytes?: number
    max_allowed_bytes?: number
    mime_type?: string
    extension?: string
  }
}
