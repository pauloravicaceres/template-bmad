import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkflowStepper from '../components/workflow/WorkflowStepper.vue'
import { buildDefaultStages } from '../composables/useWorkflow'
import type { WorkflowStageStep } from '../types'

describe('WorkflowStepper Component (T009 / US1)', () => {
  it('DebeRenderizarLas8EtapasCanonicasDelPipeline', () => {
    // Arrange
    const stages = buildDefaultStages('UX')

    // Act
    const wrapper = mount(WorkflowStepper, {
      props: {
        stages,
        activeStageKey: 'UX',
      },
    })

    // Assert
    expect(wrapper.text()).toContain('Pipeline de Agentes (Workflow Progress)')
    expect(wrapper.text()).toContain('PM')
    expect(wrapper.text()).toContain('BA')
    expect(wrapper.text()).toContain('QA')
    expect(wrapper.text()).toContain('UX')
    expect(wrapper.text()).toContain('SA')
    expect(wrapper.text()).toContain('DA')
    expect(wrapper.text()).toContain('API')
    expect(wrapper.text()).toContain('QT')
  })

  it('DebeDestacarLaEtapaActivaConBadgeEnProgreso', () => {
    // Arrange
    const stages = buildDefaultStages('DA')

    // Act
    const wrapper = mount(WorkflowStepper, {
      props: {
        stages,
        activeStageKey: 'DA',
      },
    })

    // Assert
    expect(wrapper.text()).toContain('[● EN PROGRESO]')
    const buttons = wrapper.findAll('button')
    const daButton = buttons.find((b) => b.text().includes('DA'))
    expect(daButton?.classes()).toContain('bg-blue-50')
  })

  it('TransicionReactiva_AlActualizarEtapaPorWorkflowUpdated_DebeMoverElPulsoAnimado', async () => {
    // Arrange: Etapa inicial en QA
    const initialStages = buildDefaultStages('QA')
    const wrapper = mount(WorkflowStepper, {
      props: {
        stages: initialStages,
        activeStageKey: 'QA',
      },
    })

    expect(wrapper.find('button.bg-blue-50').text()).toContain('QA')

    // Act: Evento WORKFLOW_UPDATED conmuta el turno a UX
    const updatedStages = buildDefaultStages('UX')
    await wrapper.setProps({
      stages: updatedStages,
      activeStageKey: 'UX',
    })

    // Assert: Ahora QA es completada y UX tiene el pulso activo
    expect(wrapper.find('button.bg-blue-50').text()).toContain('UX')
    const qaButton = wrapper.findAll('button').find((b) => b.text().includes('QA'))
    expect(qaButton?.classes()).toContain('bg-emerald-50')
    expect(qaButton?.text()).toContain('✓')
  })

  it('AlHacerClicEnEtapaConArtefacto_DebeEmitirEventosSelectStageYSelectArtifact', async () => {
    // Arrange
    const customStages: WorkflowStageStep[] = [
      {
        stage_key: 'BA',
        stage_name: 'Business Analyst',
        agent_role: 'Business Analyst',
        order_index: 2,
        status: 'COMPLETED',
        is_active: false,
        started_at: '2026-09-30T23:10:00Z',
        completed_at: '2026-09-30T23:14:00Z',
        origin_block_index: 2,
        generated_artifact_path: 'documents/business-analyst/002-HU_monitoreo.md',
      },
    ]

    // Act
    const wrapper = mount(WorkflowStepper, {
      props: {
        stages: customStages,
        activeStageKey: 'UX',
      },
    })

    const button = wrapper.find('button')
    await button.trigger('click')

    // Assert
    expect(wrapper.emitted('select-stage')).toBeTruthy()
    expect(wrapper.emitted('select-stage')?.[0]).toEqual([customStages[0]])
    expect(wrapper.emitted('select-artifact')).toBeTruthy()
    expect(wrapper.emitted('select-artifact')?.[0]).toEqual(['documents/business-analyst/002-HU_monitoreo.md'])
  })
})

describe('WorkflowStepper - Retrabajo SDD', () => {
  const conRetrabajo = (): WorkflowStageStep[] =>
    buildDefaultStages('CR').map((s) => {
      if (s.stage_key === 'CR') {
        return { ...s, status: 'COMPLETED', is_active: false, rework_state: 'REJECTED', rework_iteration: 1, rework_max: 2, rework_reason: 'RECHAZADO: falta ValidationBehavior' } as WorkflowStageStep
      }
      if (s.stage_key === 'DEV-BACK') {
        return { ...s, status: 'IN_PROGRESS', is_active: true, rework_state: 'REWORK', rework_iteration: 1, rework_max: 2, rework_reason: 'RECHAZADO: falta ValidationBehavior' } as WorkflowStageStep
      }
      return s
    })

  it('DebeMarcarRechazadoAlRevisorYRetrabajoALaEtapaACorregir', () => {
    const wrapper = mount(WorkflowStepper, { props: { stages: conRetrabajo(), activeStageKey: 'DEV-BACK' } })

    expect(wrapper.text()).toContain('[✗ RECHAZADO]')
    expect(wrapper.text()).toContain('[● EN PROGRESO · RETRABAJO 1/2]')
    expect(wrapper.text()).toContain('Retrabajo 1/2')
  })

  it('NoDebeMostrarBannerNiMarcasSiNoHayRetrabajo', () => {
    const wrapper = mount(WorkflowStepper, { props: { stages: buildDefaultStages('UX'), activeStageKey: 'UX' } })

    expect(wrapper.text()).not.toContain('RETRABAJO')
    expect(wrapper.text()).not.toContain('RECHAZADO')
  })
})


describe('WorkflowStepper - Etapa estancada', () => {
  it('DebeMostrarEstancadaEnLaEtapaConAlertaSinTocarLasDemas', () => {
    const stages = buildDefaultStages('QT').map((s) =>
      s.stage_key === 'QT'
        ? ({ ...s, alert_state: 'STALLED', alert_reason: '[Vigilante] qa-tech no registró' } as WorkflowStageStep)
        : s
    )
    const wrapper = mount(WorkflowStepper, { props: { stages, activeStageKey: 'QT' } })

    expect(wrapper.text()).toContain('[⚠ ESTANCADA]')
    expect((wrapper.text().match(/ESTANCADA/g) || []).length).toBe(1)
  })

  it('NoDebeMostrarEstancadaSinAlerta', () => {
    const wrapper = mount(WorkflowStepper, { props: { stages: buildDefaultStages('QT'), activeStageKey: 'QT' } })

    expect(wrapper.text()).not.toContain('ESTANCADA')
  })
})

describe('WorkflowStepper - Etapa omitida', () => {
  it('DebeMostrarOmitidaEnLaEtapaSaltadaSinTocarLasDemas', () => {
    const stages = buildDefaultStages('SA').map((s) =>
      s.stage_key === 'UX' ? ({ ...s, status: 'SKIPPED' } as WorkflowStageStep) : s
    )
    const wrapper = mount(WorkflowStepper, { props: { stages, activeStageKey: 'SA' } })

    expect(wrapper.text()).toContain('[⏭ OMITIDA]')
    expect((wrapper.text().match(/OMITIDA/g) || []).length).toBe(1)
  })

  it('NoDebeMostrarOmitidaSiNingunaEtapaFueSaltada', () => {
    const wrapper = mount(WorkflowStepper, { props: { stages: buildDefaultStages('SA'), activeStageKey: 'SA' } })

    expect(wrapper.text()).not.toContain('OMITIDA')
  })
})
