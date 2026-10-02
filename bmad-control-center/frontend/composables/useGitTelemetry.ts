import { ref, computed, onMounted, getCurrentInstance } from 'vue'
import type {
  GitStatusResponse,
  GitCommitItem,
  GitBranchItem,
  GitWorkingTree,
  WebSocketMessage,
  GitStatusEventPayload,
} from '../types'
import {
  fetchGitStatus,
  fetchGitCommits,
  fetchGitBranches,
  ApiClientError,
} from '../services/api_client'

export interface UseGitTelemetryOptions {
  apiBase?: string
  autoLoad?: boolean
  defaultLimit?: number
}

export function useGitTelemetry(options: UseGitTelemetryOptions = {}) {
  const apiBase = options.apiBase
  const defaultLimit = options.defaultLimit ?? 50
  const autoLoad = options.autoLoad ?? true

  const gitStatus = ref<GitStatusResponse | null>(null)
  const commits = ref<GitCommitItem[]>([])
  const totalCommits = ref<number>(0)
  const branches = ref<GitBranchItem[]>([])
  const selectedCommit = ref<GitCommitItem | null>(null)

  const isLoadingStatus = ref<boolean>(false)
  const isLoadingCommits = ref<boolean>(false)
  const isRepoNotFound = ref<boolean>(false)
  const error = ref<string | null>(null)

  const page = ref<number>(1)
  const limit = ref<number>(defaultLimit)
  const hasMore = ref<boolean>(false)

  // Propiedades computadas
  const isSyncing = computed<boolean>(() => gitStatus.value?.is_syncing ?? false)
  const isDetached = computed<boolean>(() => gitStatus.value?.is_detached ?? false)
  const isConflicted = computed<boolean>(() => gitStatus.value?.is_conflicted ?? false)
  const currentBranch = computed<string>(() => gitStatus.value?.current_branch ?? '')
  const totalModifiedFiles = computed<number>(() => gitStatus.value?.total_modified_files ?? 0)

  const workingTree = computed<GitWorkingTree>(() => {
    return (
      gitStatus.value?.working_tree ?? {
        staged: [],
        unstaged: [],
        untracked: [],
        conflicts: [],
      }
    )
  })

  const totalPages = computed<number>(() => {
    return Math.ceil(totalCommits.value / limit.value) || 1
  })

  const loadGitStatus = async (silent = false): Promise<void> => {
    if (!silent) isLoadingStatus.value = true
    error.value = null
    try {
      const data = await fetchGitStatus(apiBase)
      gitStatus.value = data
      isRepoNotFound.value = false
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.statusCode === 404) {
        isRepoNotFound.value = true
        gitStatus.value = null
      } else {
        error.value = err instanceof Error ? err.message : 'Error desconocido al consultar Git'
      }
    } finally {
      if (!silent) isLoadingStatus.value = false
    }
  }

  const loadCommits = async (pageNumber = 1, append = false): Promise<void> => {
    if (pageNumber < 1) pageNumber = 1
    isLoadingCommits.value = true
    error.value = null
    try {
      const offset = (pageNumber - 1) * limit.value
      const res = await fetchGitCommits(limit.value, offset, undefined, apiBase)
      if (append) {
        commits.value = [...commits.value, ...res.commits]
      } else {
        commits.value = res.commits
        if (res.commits.length > 0 && !selectedCommit.value) {
          selectedCommit.value = res.commits[0]
        }
      }
      totalCommits.value = res.total_count
      hasMore.value = res.has_more
      page.value = pageNumber
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.statusCode === 404) {
        isRepoNotFound.value = true
        commits.value = []
      } else {
        error.value = err instanceof Error ? err.message : 'Error al consultar historial de commits'
      }
    } finally {
      isLoadingCommits.value = false
    }
  }

  const loadBranches = async (): Promise<void> => {
    try {
      const res = await fetchGitBranches(apiBase)
      branches.value = res.branches
    } catch {
      // manejo silencioso de ramas
    }
  }

  const selectCommit = (commit: GitCommitItem): void => {
    selectedCommit.value = commit
  }

  const goToPage = async (targetPage: number): Promise<void> => {
    if (targetPage >= 1 && targetPage <= totalPages.value) {
      await loadCommits(targetPage, false)
    }
  }

  const nextPage = async (): Promise<void> => {
    if (page.value < totalPages.value) {
      await goToPage(page.value + 1)
    }
  }

  const prevPage = async (): Promise<void> => {
    if (page.value > 1) {
      await goToPage(page.value - 1)
    }
  }

  const loadMore = async (): Promise<void> => {
    if (hasMore.value && !isLoadingCommits.value) {
      await loadCommits(page.value + 1, true)
    }
  }

  const refreshAll = async (): Promise<void> => {
    await Promise.allSettled([
      loadGitStatus(),
      loadCommits(1, false),
      loadBranches(),
    ])
  }

  // Manejo de eventos WebSocket entrantes
  const handleWebSocketMessage = (msg: WebSocketMessage<GitStatusEventPayload> | string): void => {
    if (typeof msg !== 'object' || msg === null) return
    const evType = msg.event || msg.event_type
    if (evType === 'GIT_STATUS_CHANGED') {
      // Actualización reactiva instantánea
      loadGitStatus(true)
      loadCommits(1, false)
    }
  }

  if (getCurrentInstance() && autoLoad) {
    onMounted(() => {
      refreshAll()
    })
  }

  return {
    gitStatus,
    commits,
    totalCommits,
    branches,
    selectedCommit,
    isLoadingStatus,
    isLoadingCommits,
    isRepoNotFound,
    isSyncing,
    isDetached,
    isConflicted,
    currentBranch,
    totalModifiedFiles,
    workingTree,
    page,
    limit,
    totalPages,
    hasMore,
    error,
    loadGitStatus,
    loadCommits,
    loadBranches,
    selectCommit,
    goToPage,
    nextPage,
    prevPage,
    loadMore,
    refreshAll,
    handleWebSocketMessage,
  }
}
