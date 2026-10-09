<template>
  <div>
    <section class="p-4 bg-gray-900 text-white border-b border-gray-700" aria-label="Proyectos BMAD">
      <div class="flex items-center justify-between gap-4">
        <h1 class="font-semibold">BMAD · Workspaces</h1>
        <button type="button" class="underline text-sm" @click="loadProjects">Actualizar proyectos</button>
      </div>
      <p v-if="error" role="alert" class="mt-3">{{ error }}</p>
      <p v-else-if="loading" class="mt-3">Cargando proyectos…</p>
      <template v-else>
        <p v-if="selected?.project_id" class="mt-3">Proyecto seleccionado: {{ selected.project_name }} ({{ selected.project_id }})</p>
        <p v-else class="mt-3">No hay un proyecto seleccionado.</p>
        <p v-if="!projects.length" class="mt-2">No hay proyectos registrados. Inicializa un workspace y añádelo al registro projects de config_bmad.json.</p>
        <ul v-else class="mt-3 space-y-2">
          <li v-for="project in projects" :key="project.project_id">
            <strong>{{ project.project_id }}</strong> · {{ project.workspace_root }}
            <span v-if="project.selected"> · Seleccionado</span>
          </li>
        </ul>
        <p v-if="!selected?.project_id" class="mt-3 text-sm">Para supervisarlo, inicia su backend con BMAD_PROJECT o BMAD_WORKSPACE y conecta esta consola mediante VITE_BMAD_API_BASE.</p>
      </template>
    </section>
    <WorkspaceDashboard v-if="selected?.project_id" :key="selected.project_id" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import WorkspaceDashboard from '../components/WorkspaceDashboard.vue'
import { DEFAULT_API_BASE } from '../services/api_client'

interface Project { project_id: string; workspace_root: string; selected: boolean }
interface SelectedProject { project_id: string | null; project_name: string }
const projects = ref<Project[]>([])
const selected = ref<SelectedProject | null>(null)
const loading = ref(true)
const error = ref('')

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const [projectResponse, registryResponse] = await Promise.all([
      fetch(`${DEFAULT_API_BASE}/project`), fetch(`${DEFAULT_API_BASE}/projects`),
    ])
    if (!projectResponse.ok || !registryResponse.ok) throw new Error('No se pudo consultar el registro de proyectos.')
    selected.value = await projectResponse.json()
    projects.value = (await registryResponse.json()).projects
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'No se pudo conectar con el backend BMAD.'
    selected.value = null
  } finally {
    loading.value = false
  }
}
onMounted(loadProjects)
</script>
