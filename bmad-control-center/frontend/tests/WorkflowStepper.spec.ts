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
