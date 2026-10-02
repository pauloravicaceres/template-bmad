import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GitRepoEmptyState from '../components/git/GitRepoEmptyState.vue'
import GitLockWarningBanner from '../components/git/GitLockWarningBanner.vue'

describe('Git Resilience Components (Empty State & Lock Banner)', () => {
  describe('GitRepoEmptyState Component', () => {
    it('DebeRenderizarMensajesInformativosYComandoSugerido', () => {
      // Act
      const wrapper = mount(GitRepoEmptyState)

      // Assert
      expect(wrapper.text()).toContain('Repositorio Git No Detectado')
      expect(wrapper.text()).toContain('.git/')
      expect(wrapper.text()).toContain('Centro de Comando HITL')
      expect(wrapper.text()).toContain('git init && git add .')
    })

    it('AlHacerClicEnReintentar_DebeEmitirRetry', async () => {
      // Act
      const wrapper = mount(GitRepoEmptyState)
      const retryBtn = wrapper.findAll('button').find((b) => b.text().includes('Reintentar Detección'))
      await retryBtn?.trigger('click')

      // Assert
      expect(wrapper.emitted('retry')).toBeTruthy()
    })

    it('AlHacerClicEnIrAArtefactos_DebeEmitirGoToArtifacts', async () => {
      // Act
      const wrapper = mount(GitRepoEmptyState)
      const navBtn = wrapper.findAll('button').find((b) => b.text().includes('Ir al Explorador de Artefactos'))
      await navBtn?.trigger('click')

      // Assert
      expect(wrapper.emitted('go-to-artifacts')).toBeTruthy()
    })
  })

  describe('GitLockWarningBanner Component', () => {
    it('CuandoIsSyncingEsTrue_DebeMostrarBannerDeAviso', () => {
      // Act
      const wrapper = mount(GitLockWarningBanner, {
        props: { isSyncing: true },
      })

      // Assert
      expect(wrapper.text()).toContain('TRANSACCIÓN GIT EN CURSO')
      expect(wrapper.text()).toContain('.git/index.lock detectado')
      expect(wrapper.text()).toContain('Sincronización Automática')
    })

    it('CuandoIsSyncingEsFalse_NoDebeMostrarBanner', () => {
      // Act
      const wrapper = mount(GitLockWarningBanner, {
        props: { isSyncing: false },
      })

      // Assert
      expect(wrapper.find('div[role="alert"]').exists()).toBe(false)
    })
  })
})
