import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GitLockWarningBanner from '../components/git/GitLockWarningBanner.vue'
import GitRepoEmptyState from '../components/git/GitRepoEmptyState.vue'
import GitWorkingTreeClassifier from '../components/git/GitWorkingTreeClassifier.vue'
import GitBinaryDiffNotice from '../components/git/GitBinaryDiffNotice.vue'
import type { GitWorkingTree } from '../types'

describe('Git Telemetry & VCS Components (HU-004 QA Certification)', () => {
  describe('GitLockWarningBanner Component (SC-03 / CB-01 / ADR-015)', () => {
    it('Render_CuandoIsSyncingEsTrue_DebeMostrarBannerDeAlertaConMensajeDeContencion', () => {
      // Arrange
      const isSyncing = true

      // Act
      const wrapper = mount(GitLockWarningBanner, {
        props: { isSyncing },
      })

      // Assert
      expect(wrapper.text()).toContain('TRANSACCIÓN GIT EN CURSO (.git/index.lock detectado)')
      expect(wrapper.text()).toContain('[ ⏳ Sincronización Automática ]')
      expect(wrapper.text()).toContain('despliega de forma segura el último snapshot cacheado')
    })

    it('Render_CuandoIsSyncingEsFalse_NoDebeMostrarBanner', () => {
      // Arrange
      const isSyncing = false

      // Act
      const wrapper = mount(GitLockWarningBanner, {
        props: { isSyncing },
      })

      // Assert
      expect(wrapper.find('div[role="alert"]').exists()).toBe(false)
    })
  })

  describe('GitRepoEmptyState Component (SC-04 / CB-02)', () => {
    it('Render_CuandoRepoNoExiste_DebeMostrarMensajeInstructivoYComandoGitInit', () => {
      // Arrange & Act
      const wrapper = mount(GitRepoEmptyState)

      // Assert
      expect(wrapper.text()).toContain('Repositorio Git No Detectado')
      expect(wrapper.text()).toContain('.git/')
      expect(wrapper.text()).toContain('git init && git add .')
      expect(wrapper.text()).toContain('Centro de Comando HITL')
      expect(wrapper.text()).toContain('Monitor de Workflow y Explorador de Artefactos')
    })

    it('Click_EnBotonReintentar_DebeEmitirEventoRetry', async () => {
      // Arrange
      const wrapper = mount(GitRepoEmptyState)

      // Act
      const retryBtn = wrapper.findAll('button').find((b) => b.text().includes('Reintentar Detección'))
      expect(retryBtn).toBeDefined()
      await retryBtn!.trigger('click')

      // Assert
      expect(wrapper.emitted('retry')).toBeTruthy()
      expect(wrapper.emitted('retry')!.length).toBe(1)
    })

    it('Click_EnBotonIrAArtefactos_DebeEmitirEventoGoToArtifacts', async () => {
      // Arrange
      const wrapper = mount(GitRepoEmptyState)

      // Act
      const navBtn = wrapper.findAll('button').find((b) => b.text().includes('Ir al Explorador de Artefactos'))
      expect(navBtn).toBeDefined()
      await navBtn!.trigger('click')

      // Assert
      expect(wrapper.emitted('go-to-artifacts')).toBeTruthy()
      expect(wrapper.emitted('go-to-artifacts')!.length).toBe(1)
    })
  })

  describe('GitWorkingTreeClassifier Component (SC-01)', () => {
    it('Render_ConRepositorioLimpio_DebeMostrarMensajeInformativoDeRepositorioLimpio', () => {
      // Arrange
      const workingTree = {
        staged: [],
        unstaged: [],
        untracked: [],
        conflicts: [],
      }

      // Act
      const wrapper = mount(GitWorkingTreeClassifier, {
        props: { workingTree },
      })

      // Assert
      expect(wrapper.text()).toContain('Área de Trabajo (Working Directory)')
      expect(wrapper.text()).toContain('Total: 0 mutaciones')
      expect(wrapper.text()).toContain('✨ Repositorio limpio. No hay modificaciones en el área de trabajo.')
    })

    it('Render_ConArchivosStagedUnstagedYConflictos_DebeDesplegarSeccionesTripartitasConConteo', () => {
      // Arrange
      const workingTree = {
        staged: [
          { relative_path: 'bmad-control-center/backend/main.py', status_code: 'M', category: 'staged' as const },
        ],
        unstaged: [
          { relative_path: 'files/tracker_bmad.md', status_code: 'M', category: 'unstaged' as const },
        ],
        untracked: [
          { relative_path: 'scratch/test.txt', status_code: '?', category: 'untracked' as const },
        ],
        conflicts: [
          { relative_path: 'specs/README.md', status_code: 'U', category: 'conflict' as const },
        ],
      }

      // Act
      const wrapper = mount(GitWorkingTreeClassifier, {
        props: { workingTree },
      })

      // Assert
      expect(wrapper.text()).toContain('Total: 4 mutaciones')
      expect(wrapper.text()).toContain('🔴 ARCHIVOS EN CONFLICTO (1)')
      expect(wrapper.text()).toContain('🟢 STAGED CHANGES (1)')
      expect(wrapper.text()).toContain('🟡 UNSTAGED CHANGES (1)')
      expect(wrapper.text()).toContain('⚪ UNTRACKED FILES (1)')
    })
  })

  describe('GitBinaryDiffNotice Component (CB-05 / ADR-014)', () => {
    it('Render_ConArchivoBinarioMayorA1MB_DebeMostrarInsigniaDeDiffOmitidoYTamanoFormateado', () => {
      // Arrange
      const filePath = 'files/designer-ux/mockup.png'
      const sizeBytes = 2500000 // ~2.38 MB

      // Act
      const wrapper = mount(GitBinaryDiffNotice, {
        props: { filePath, sizeBytes },
      })

      // Assert
      expect(wrapper.text()).toContain('files/designer-ux/mockup.png')
      expect(wrapper.text()).toContain('[ ARCHIVO BINARIO - DIFF TEXTUAL OMITIDO ]')
      expect(wrapper.text()).toContain('2.38 MB')
      expect(wrapper.text()).toContain('Se omitió el desglose línea por línea para proteger el rendimiento')
    })
  })
})
