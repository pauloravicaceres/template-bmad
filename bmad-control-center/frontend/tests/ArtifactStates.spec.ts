import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ArtifactEmptyState from '../components/artifacts/ArtifactEmptyState.vue'
import ArtifactErrorCard from '../components/artifacts/ArtifactErrorCard.vue'
import type { ApiClientError } from '../services/api_client'

describe('ArtifactStates & Error Handling Components (HU-002 QA Certification)', () => {
  describe('ArtifactEmptyState Component (SC-05 / CB-05)', () => {
    it('Render_ConDirectorioVacioYRolAgente_DebeMostrarTarjetaInformativaYEstadoEnEspera', () => {
      // Arrange
      const folderPath = 'docs/solutions-architect'
      const agentRole = 'Solutions Architect'
      const stageStatus = 'En progreso agéntico'

      // Act
      const wrapper = mount(ArtifactEmptyState, {
        props: {
          folderPath,
          agentRole,
          stageStatus,
        },
      })

      // Assert
      expect(wrapper.text()).toContain('[ 📁 ETAPA SIN ENTREGABLES ]')
      expect(wrapper.text()).toContain("El agente 'Solutions Architect'")
      expect(wrapper.text()).toContain('En progreso agéntico')
      expect(wrapper.text()).toContain('docs/solutions-architect')
      expect(wrapper.text()).toContain('0 archivos encontrados')
    })

    it('Render_SinProps_DebeMostrarFallbackGenericoSinRomperComponente', () => {
      // Arrange & Act
      const wrapper = mount(ArtifactEmptyState, {
        props: {},
      })

      // Assert
      expect(wrapper.text()).toContain('[ 📁 ETAPA SIN ENTREGABLES ]')
      expect(wrapper.text()).toContain("El agente 'Agente Asignado'")
      expect(wrapper.text()).toContain('En espera de turno agéntico')
      expect(wrapper.find('.font-mono').exists()).toBe(false)
    })

    it('Render_ConRutaDeCarpetaSinRol_DebeInferirRolDeAgenteDesdeRuta', () => {
      // Arrange
      const folderPath = 'docs/business-analyst'

      // Act
      const wrapper = mount(ArtifactEmptyState, {
        props: {
          folderPath,
        },
      })

      // Assert
      expect(wrapper.text()).toContain("El agente 'Business Analyst'")
      expect(wrapper.text()).toContain('docs/business-analyst')
    })
  })

  describe('ArtifactErrorCard Component (SC-02, SC-04, CB-04)', () => {
    it('Render_ConError404_DebeMostrarTarjetaAmbarYBotonActualizarArbol', () => {
      // Arrange
      const error: ApiClientError = {
        name: 'ApiClientError',
        message: 'El archivo solicitado ya no existe en el disco.',
        statusCode: 404,
        errorCode: 'ARTIFACT_NOT_FOUND',
        path: 'docs/product-analyst/inexistente.md',
      }

      // Act
      const wrapper = mount(ArtifactErrorCard, {
        props: {
          error,
          requestedPath: 'docs/product-analyst/inexistente.md',
          hasLastValid: true,
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Artefacto No Encontrado (HTTP 404)')
      expect(wrapper.text()).toContain('docs/product-analyst/inexistente.md')
      expect(wrapper.text()).toContain('Actualizar Árbol de Artefactos')
      expect(wrapper.text()).toContain('Volver al Último Válido')
    })

    it('Render_ConError403PathTraversal_DebeMostrarTarjetaRojaDeSeguridadYExplicacionSandbox', () => {
      // Arrange
      const error: ApiClientError = {
        name: 'ApiClientError',
        message: 'Acceso denegado por violación de Sandbox.',
        statusCode: 403,
        errorCode: 'PATH_TRAVERSAL_DETECTED',
        path: '../../etc/passwd',
      }

      // Act
      const wrapper = mount(ArtifactErrorCard, {
        props: {
          error,
          requestedPath: '../../etc/passwd',
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Acceso Denegado por Seguridad (HTTP 403 Forbidden)')
      expect(wrapper.text()).toContain('../../etc/passwd')
      expect(wrapper.text()).toContain('POLÍTICA DE SEGURIDAD DEL ESPACIO DE TRABAJO')
      expect(wrapper.text()).toContain('docs/ (Entregables y artefactos agénticos)')
    })

    it('Render_ConError413PayloadDemasiadoGrande_DebeMostrarAdvertenciaDe5MB', () => {
      // Arrange
      const error: ApiClientError = {
        name: 'ApiClientError',
        message: 'El archivo excede los 5MB autorizados.',
        statusCode: 413,
        errorCode: 'PAYLOAD_TOO_LARGE',
        path: 'docs/data-architect/huge_dump.sql',
        metadata: { size_bytes: 8388608 },
      }

      // Act
      const wrapper = mount(ArtifactErrorCard, {
        props: {
          error,
          requestedPath: 'docs/data-architect/huge_dump.sql',
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Archivo No Renderizable en Modo Texto (HTTP 413)')
      expect(wrapper.text()).toContain('docs/data-architect/huge_dump.sql')
      expect(wrapper.text()).toContain('excede el límite máximo de previsualización (5 MB)')
      expect(wrapper.text()).toContain('8 MB')
    })

    it('Render_ConError415FormatoBinarioNoSoportado_DebeMostrarAdvertenciaDeFormatoBinario', () => {
      // Arrange
      const error: ApiClientError = {
        name: 'ApiClientError',
        message: 'El archivo binario no es soportado.',
        statusCode: 415,
        errorCode: 'UNSUPPORTED_MEDIA_TYPE',
        path: 'docs/designer-ux/mockup.png',
      }

      // Act
      const wrapper = mount(ArtifactErrorCard, {
        props: {
          error,
          requestedPath: 'docs/designer-ux/mockup.png',
        },
      })

      // Assert
      expect(wrapper.text()).toContain('Archivo No Renderizable en Modo Texto (HTTP 415)')
      expect(wrapper.text()).toContain('docs/designer-ux/mockup.png')
      expect(wrapper.text()).toContain('posee un formato binario no representable en modo texto')
    })

    it('Click_EnBotonActualizarArbol_DebeEmitirEventoRefreshTree', async () => {
      // Arrange
      const error: ApiClientError = {
        name: 'ApiClientError',
        message: 'No encontrado',
        statusCode: 404,
        errorCode: 'ARTIFACT_NOT_FOUND',
        path: 'docs/qa-tech/missing.md',
      }
      const wrapper = mount(ArtifactErrorCard, {
        props: {
          error,
          requestedPath: 'docs/qa-tech/missing.md',
        },
      })

      // Act
      const refreshBtn = wrapper.findAll('button').find((b) => b.text().includes('Actualizar Árbol de Artefactos'))
      expect(refreshBtn).toBeDefined()
      await refreshBtn!.trigger('click')

      // Assert
      expect(wrapper.emitted('refresh-tree')).toBeTruthy()
      expect(wrapper.emitted('refresh-tree')!.length).toBe(1)
    })
  })
})
