import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useGitTelemetry } from '../composables/useGitTelemetry'
import * as apiClient from '../services/api_client'
import type { GitStatusResponse, GitCommitListResponse, GitBranchListResponse } from '../types'

vi.mock('../services/api_client', async () => {
  const actual = await vi.importActual('../services/api_client')
  return {
    ...actual,
    fetchGitStatus: vi.fn(),
    fetchGitCommits: vi.fn(),
    fetchGitBranches: vi.fn(),
  }
})

describe('useGitTelemetry Composable', () => {
  const mockStatus: GitStatusResponse = {
    current_branch: 'feat/004-HU_panel_telemetria_control_versiones_git',
    head_commit_hash: 'a7c4e91d830b8ef29e92d77cb31940918ef83921',
    head_commit_short: 'a7c4e91',
    head_commit_message: 'feat(git): add spec for telemetry panel',
    head_commit_author: 'Business Analyst',
    head_committed_at: '2026-10-01T08:06:15Z',
    upstream_branch: 'dev',
    is_detached: false,
    is_conflicted: false,
    is_syncing: false,
    staged_count: 2,
    unstaged_count: 1,
    untracked_count: 1,
    total_modified_files: 4,
    working_tree: {
      staged: [],
      unstaged: [],
      untracked: [],
      conflicts: [],
    },
    captured_at_utc: '2026-10-01T08:42:00Z',
  }

  const mockCommitsRes: GitCommitListResponse = {
    commits: [
      {
        commit_hash: 'a7c4e91d830b8ef29e92d77cb31940918ef83921',
        short_hash: 'a7c4e91',
        author_name: 'Business Analyst',
        author_email: 'ba@bmad.local',
        committed_at: '2026-10-01T08:06:15Z',
        message: 'feat(git): add spec for telemetry panel',
        files_changed_count: 2,
        insertions: 239,
        deletions: 0,
      },
      {
        commit_hash: '9f3e2b0c1a8d4e7f6b5c3d2e1f0a9b8c7d6e5f4a',
        short_hash: '9f3e2b0',
        author_name: 'Watcher BMAD',
        author_email: 'watcher@bmad.local',
        committed_at: '2026-10-01T07:59:45Z',
        message: 'merge: close branch feat/003',
        files_changed_count: 1,
        insertions: 10,
        deletions: 5,
      },
    ],
    total_count: 120,
    limit: 50,
    offset: 0,
    has_more: true,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.fetchGitStatus).mockResolvedValue(mockStatus)
    vi.mocked(apiClient.fetchGitCommits).mockResolvedValue(mockCommitsRes)
    vi.mocked(apiClient.fetchGitBranches).mockResolvedValue({
      current_branch: 'feat/004',
      total_branches: 1,
      branches: [],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('AlEjecutarLoadGitStatus_DebeActualizarEstadoYPropiedadesComputadas', async () => {
    // Arrange
    const { loadGitStatus, gitStatus, currentBranch, totalModifiedFiles, isSyncing } =
      useGitTelemetry({ autoLoad: false })

    // Act
    await loadGitStatus()

    // Assert
    expect(gitStatus.value).toEqual(mockStatus)
    expect(currentBranch.value).toBe('feat/004-HU_panel_telemetria_control_versiones_git')
    expect(totalModifiedFiles.value).toBe(4)
    expect(isSyncing.value).toBe(false)
  })

  it('AlRetornar404EnGitStatus_DebeActivarIsRepoNotFound', async () => {
    // Arrange
    vi.mocked(apiClient.fetchGitStatus).mockRejectedValueOnce(
      new apiClient.ApiClientError(
        'Repositorio no encontrado',
        'GIT_REPO_NOT_FOUND',
        404,
        new Date().toISOString(),
        '/git/status'
      )
    )

    const { loadGitStatus, gitStatus, isRepoNotFound } = useGitTelemetry({ autoLoad: false })

    // Act
    await loadGitStatus()

    // Assert
    expect(isRepoNotFound.value).toBe(true)
    expect(gitStatus.value).toBeNull()
  })

  it('AlCargarCommits_DebeActualizarListaYSeleccionarPrimerCommitPorDefecto', async () => {
    // Arrange
    const { loadCommits, commits, totalCommits, selectedCommit, totalPages, hasMore } =
      useGitTelemetry({ autoLoad: false, defaultLimit: 50 })

    // Act
    await loadCommits(1, false)

    // Assert
    expect(commits.value).toHaveLength(2)
    expect(totalCommits.value).toBe(120)
    expect(selectedCommit.value?.short_hash).toBe('a7c4e91')
    expect(totalPages.value).toBe(3) // 120 / 50 = 2.4 => 3
    expect(hasMore.value).toBe(true)
  })

  it('AlPaginatConNextPageYGoToPage_DebeInvocarApiConOffsetCorrecto', async () => {
    // Arrange
    const { loadCommits, nextPage, page } = useGitTelemetry({
      autoLoad: false,
      defaultLimit: 50,
    })
    await loadCommits(1, false)
    expect(page.value).toBe(1)

    // Act
    await nextPage()

    // Assert
    expect(apiClient.fetchGitCommits).toHaveBeenCalledWith(50, 50, undefined, undefined)
    expect(page.value).toBe(2)
  })

  it('AlRecibirEventoWebSocketGitStatusChanged_DebeRefrescarEstadoYCommits', async () => {
    // Arrange
    const { handleWebSocketMessage, gitStatus } = useGitTelemetry({ autoLoad: false })
    expect(gitStatus.value).toBeNull()

    // Act
    handleWebSocketMessage({
      event_type: 'GIT_STATUS_CHANGED',
      payload: {
        current_branch: 'dev',
        head_hash_short: '1234567',
        is_detached: false,
        is_conflicted: false,
        is_syncing: false,
        staged_count: 0,
        unstaged_count: 0,
        untracked_count: 0,
        total_modified_files: 0,
      },
    })

    // Assert - Silently triggers fetch
    expect(apiClient.fetchGitStatus).toHaveBeenCalled()
    expect(apiClient.fetchGitCommits).toHaveBeenCalled()
  })
})
