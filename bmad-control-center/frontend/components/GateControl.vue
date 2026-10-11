<template>
  <div class="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md space-y-4">
    <h2 class="text-xl font-bold">Estado: {{ status }}</h2>
    <div v-if="status === 'PENDING_DECISION'" class="space-y-4">
      <p>Hay una compuerta esperando decisión.</p>

      <textarea 
        v-model="feedback"
        class="w-full border rounded p-2"
        placeholder="Feedback (Obligatorio para rechazar)"
      ></textarea>
      <div class="flex space-x-2">
        <button 
          @click="approve"
          class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded w-full"
        >
          Aprobar
        </button>
        <button 
          @click="reject"
          :disabled="!feedback.trim()"
          class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded w-full disabled:opacity-50"
        >
          Rechazar
        </button>
      </div>
      <p v-if="error" role="alert" class="text-red-600 text-sm">{{ error }}</p>
    </div>
    <div v-else>
      <p>Todo en orden, sin compuertas pendientes.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { DEFAULT_API_BASE } from '../services/api_client'

const status = ref('UNKNOWN')
const gateId = '123'
const feedback = ref('')
const error = ref('')

// El backend rechaza la decisión (p. ej. identificador de HU inválido) con 4xx y su motivo en `detail`.
const decisionError = async (res) => {
  if (!res || res.ok !== false) return ''
  try {
    return (await res.json()).detail || `Error ${res.status}`
  } catch (e) {
    return `Error ${res.status}`
  }
}

const fetchStatus = async () => {
  try {
    const res = await fetch(`${DEFAULT_API_BASE}/gates/status`)
    const data = await res.json()
    status.value = data.status
  } catch (e) {
    console.error(e)
  }
}

const approve = async () => {
  try {
    const res = await fetch(`${DEFAULT_API_BASE}/gates/${gateId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'APPROVE', feedback: feedback.value })
    })
    error.value = await decisionError(res)
    fetchStatus()
  } catch (e) {
    console.error(e)
  }
}

const reject = async () => {
  try {
    const res = await fetch(`${DEFAULT_API_BASE}/gates/${gateId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'REJECT', feedback: feedback.value })
    })
    error.value = await decisionError(res)
    feedback.value = ''
    fetchStatus()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchStatus()
})
</script>
