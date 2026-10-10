import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PerimeterSecurityCard from '../components/observability/PerimeterSecurityCard.vue'
import LargeFileMetadataCard from '../components/observability/LargeFileMetadataCard.vue'
import EventLogStream from '../components/observability/EventLogStream.vue'
import type { PerimeterStatusResponse, FileMetadataRecord, WebSocketEventEnvelope } from '../types'

describe('Observability & Notification Components (HU-003 QA Certification)', () => {
  describe('PerimeterSecurityCard Component (SC-05 / ADR-012)', () => {
    it('Render_ConEstadoPerimetral_DebeMostrarRaicesAutorizadasYContadorDeDescartes', () => {
      // Arrange
      const mockStatus: PerimeterStatusResponse = {
        perimeter_active: true,
        allowed_roots: ['docs', 'specs', '.specify'],
        ignored_external_events_count: 14,
        policy: 'STRICT_FSaaDB_SANDBOX',
        monitored_paths_count: 3,
      }

      // Act
      const wrapper = mount(PerimeterSecurityCard, {
        props: {
          perimeterStatus: mockStatus,
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Perímetro de Seguridad (Sandbox FSaaDB)')
      expect(wrapper.text()).toContain('0 Fugas (Criterio SC-004)')
      expect(wrapper.text()).toContain('[✓] docs')
      expect(wrapper.text()).toContain('[✓] specs')
      expect(wrapper.text()).toContain('[✓] .specify')
      expect(wrapper.text()).toContain('14 eventos')
    })

    it('Render_SinProps_DebeMostrarValoresPorDefectoSinRomper', () => {
      // Arrange & Act
      const wrapper = mount(PerimeterSecurityCard, {
        props: {},
      })

      // Assert
      expect(wrapper.text()).toContain('Perímetro de Seguridad')
      expect(wrapper.text()).toContain('[✓] docs')
      expect(wrapper.text()).toContain('0 eventos')
    })
  })

  describe('LargeFileMetadataCard Component (CB-05 / ADR-012)', () => {
    it('Render_ConMetadatosDeArchivoExtenso_DebeMostrarAdvertenciaDe5MBYTamanoFormateado', () => {
      // Arrange
      const mockMetadata: FileMetadataRecord = {
        relative_path: 'docs/data-architect/huge_database_dump.sql',
        filename: 'huge_database_dump.sql',
        size_bytes: 8388608, // 8 MB
        mime_type: 'application/sql',
        is_large_file: true,
        metadata_only: true,
        updated_at: '2026-10-01T02:30:00Z',
      }

      // Act
      const wrapper = mount(LargeFileMetadataCard, {
        props: {
          metadata: mockMetadata,
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Artefacto Extenso Detectado (Política Metadata-Only)')
      expect(wrapper.text()).toContain('docs/data-architect/huge_database_dump.sql')
      expect(wrapper.text()).toContain('8 MB')
      expect(wrapper.text()).toContain('application/sql')
      expect(wrapper.text()).toContain('excede el umbral máximo de previsualización web (5 MB)')
      expect(wrapper.text()).toContain('Volver al Explorador de Archivos')
    })

    it('Click_EnBotonVolver_DebeEmitirEventoBack', async () => {
      // Arrange
      const wrapper = mount(LargeFileMetadataCard, {
        props: {
          requestedPath: 'docs/test.log',
        },
      })

      // Act
      const backBtn = wrapper.find('button')
      expect(backBtn.exists()).toBe(true)
      await backBtn.trigger('click')

      // Assert
      expect(wrapper.emitted('back')).toBeTruthy()
      expect(wrapper.emitted('back')!.length).toBe(1)
    })
  })

  describe('EventLogStream Component (SC-01, SC-02, SC-04)', () => {
    it('Render_SinEventos_DebeMostrarMensajeDeEspera', () => {
      // Arrange & Act
      const wrapper = mount(EventLogStream, {
        props: {
          events: [],
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Log de Eventos en Vivo (WS Stream)')
      expect(wrapper.text()).toContain('0 eventos')
      expect(wrapper.text()).toContain('En espera de eventos en tiempo real...')
    })

    it('Render_ConListaDeEventos_DebeDesplegarTipoDeEventoRecursoYBadgesDeCoalescencia', () => {
      // Arrange
      const mockEvents: WebSocketEventEnvelope[] = [
        {
          event_id: 'ev-1',
          event_type: 'WORKFLOW_UPDATED',
          resource_path: 'docs/tracker_bmad.md',
          timestamp: '2026-10-01T02:35:00Z',
          coalesced_count: 1,
          payload: {
            active_stage: 'QA',
            agent_role: 'QA Documental',
          },
        },
        {
          event_id: 'ev-2',
          event_type: 'ARTIFACT_CHANGED',
          resource_path: 'docs/business-analyst/003-HU.md',
          timestamp: '2026-10-01T02:36:00Z',
          coalesced_count: 5, // Coalescencia múltiple (SC-04 / CB-02)
          payload: {
            change_type: 'modified',
          },
        },
      ]

      // Act
      const wrapper = mount(EventLogStream, {
        props: {
          events: mockEvents,
        },
      })

      // Assert
      expect(wrapper.text()).toContain('2 eventos')
      expect(wrapper.text()).toContain('WORKFLOW_UPDATED')
      expect(wrapper.text()).toContain('docs/tracker_bmad.md')
      expect(wrapper.text()).toContain('QA Documental')
      expect(wrapper.text()).toContain('ARTIFACT_CHANGED')
      expect(wrapper.text()).toContain('docs/business-analyst/003-HU.md')
      expect(wrapper.text()).toContain('⚡ Coalescencia: 5 mutaciones')
    })
  })
})
