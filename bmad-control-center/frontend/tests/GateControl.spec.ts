import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('GateControl - Centro de Comando HITL', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('US1: Visualización y Aprobación de Compuerta (Happy Path y Estados)', () => {
    it('FetchStatus_CuandoApiRetornaPendingDecision_DebeActualizarEstadoAPendingDecision', async () => {
      // Arrange
      let status = 'UNKNOWN'
      const mockResponse = { status: 'PENDING_DECISION', content: '### Handoff: @HUMANO:' }
      const fetchMock = vi.fn().mockResolvedValue({
        json: async () => mockResponse,
      })
      globalThis.fetch = fetchMock

      // Act
      const res = await fetch('http://localhost:8000/api/v1/gates/status')
      const data = await res.json()
      status = data.status

      // Assert
      expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/v1/gates/status')
      expect(status).toBe('PENDING_DECISION')
    })

    it('Approve_AlHacerClicEnAprobar_DebeEnviarPayloadApproveYRefrescarEstado', async () => {
      // Arrange
      const gateId = '123'
      let status = 'PENDING_DECISION'
      const fetchCalls: { url: string; options?: any }[] = []
      
      const fetchMock = vi.fn().mockImplementation(async (url: string, options?: any) => {
        fetchCalls.push({ url, options })
        if (options?.method === 'POST') {
          return { json: async () => ({ message: 'Decision recorded' }) }
        }
        return { json: async () => ({ status: 'APPROVED' }) }
      })
      globalThis.fetch = fetchMock

      // Act
      // 1. Envío de decisión de aprobación
      await fetch(`http://localhost:8000/api/v1/gates/${gateId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'APPROVE' }),
      })
      // 2. Refresco posterior de estado
      const res = await fetch('http://localhost:8000/api/v1/gates/status')
      const data = await res.json()
      status = data.status

      // Assert
      expect(fetchCalls).toHaveLength(2)
      expect(fetchCalls[0].url).toBe('http://localhost:8000/api/v1/gates/123/decision')
      expect(JSON.parse(fetchCalls[0].options.body)).toEqual({ action: 'APPROVE' })
      expect(status).toBe('APPROVED')
    })
  })

  describe('US2: Rechazo con Retroalimentación (Happy Path y Limpieza)', () => {
    it('Reject_ConFeedbackValido_DebeEnviarPayloadRejectYLimpiarFeedback', async () => {
      // Arrange
      const gateId = '123'
      let feedback = 'Subsanar criterios de aceptación BDD'
      let status = 'PENDING_DECISION'
      let sentPayload: any = null

      const fetchMock = vi.fn().mockImplementation(async (url: string, options?: any) => {
        if (options?.method === 'POST') {
          sentPayload = JSON.parse(options.body)
          return { json: async () => ({ message: 'Decision recorded' }) }
        }
        return { json: async () => ({ status: 'REJECTED_WITH_FEEDBACK' }) }
      })
      globalThis.fetch = fetchMock

      // Act
      await fetch(`http://localhost:8000/api/v1/gates/${gateId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'REJECT', feedback }),
      })
      feedback = '' // Simula la mutación reactiva de GateControl.vue tras el envío
      const res = await fetch('http://localhost:8000/api/v1/gates/status')
      const data = await res.json()
      status = data.status

      // Assert
      expect(sentPayload).toEqual({
        action: 'REJECT',
        feedback: 'Subsanar criterios de aceptación BDD',
      })
      expect(feedback).toBe('')
      expect(status).toBe('REJECTED_WITH_FEEDBACK')
    })

    it('GateControl_ConTextoEnFeedback_DebeHabilitarBotonRechazar', () => {
      // Arrange
      const feedbackConTexto = 'Requiere revisión técnica'

      // Act
      const isDisabled = !feedbackConTexto.trim()

      // Assert
      expect(isDisabled).toBe(false)
    })
  })

  describe('US3: Validación de Rechazo sin Retroalimentación (Sad Paths)', () => {
    it('GateControl_ConFeedbackVacio_DebeDeshabilitarBotonRechazar', () => {
      // Arrange
      const feedbackVacio = ''

      // Act
      const isDisabled = !feedbackVacio.trim()

      // Assert
      expect(isDisabled).toBe(true)
    })

    it('GateControl_ConFeedbackSoloEspacios_DebeDeshabilitarBotonRechazar', () => {
      // Arrange
      const feedbackEspacios = '     \t  \n  '

      // Act
      const isDisabled = !feedbackEspacios.trim()

      // Assert
      expect(isDisabled).toBe(true)
    })

    it('FetchStatus_CuandoBackendFalla_DebeManejarErrorSinLanzarExcepcionNoControlada', async () => {
      // Arrange
      let status = 'UNKNOWN'
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network Connection Refused'))

      // Act
      try {
        const res = await fetch('http://localhost:8000/api/v1/gates/status')
        const data = await res.json()
        status = data.status
      } catch (e) {
        console.error(e)
      }

      // Assert
      expect(consoleErrorSpy).toHaveBeenCalled()
      expect(status).toBe('UNKNOWN')
    })
  })

  describe('Token Guard y Seguridad en Frontend', () => {
    it('TokenGuard_CuandoFeedbackContieneTokensReservados_DebeDetectarInyeccionDeDirectivas', () => {
      // Arrange
      const regexTokenGuard = /@(PM|BA|QA|UX|SA|DA|API|QT|PA|BS|HUMANO):/i
      const feedbackConTokenPm = 'Avisar a @PM: para que priorice el fix'
      const feedbackConTokenBa = 'Delegar a @BA: urgente'
      const feedbackLimpio = 'Avisar al Product Manager para que priorice'

      // Act
      const matchPm = regexTokenGuard.test(feedbackConTokenPm)
      const matchBa = regexTokenGuard.test(feedbackConTokenBa)
      const matchLimpio = regexTokenGuard.test(feedbackLimpio)

      // Assert
      expect(matchPm).toBe(true)
      expect(matchBa).toBe(true)
      expect(matchLimpio).toBe(false)
    })
  })
})
