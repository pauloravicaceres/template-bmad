import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import Tree from 'primevue/tree'
import Button from 'primevue/button'
import Toast from 'primevue/toast'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(PrimeVue, {
    theme: {
      preset: Aura,
      options: {
        darkModeSelector: false,
      },
    },
  })
  nuxtApp.vueApp.use(ToastService)
  nuxtApp.vueApp.component('Tree', Tree)
  nuxtApp.vueApp.component('Button', Button)
  nuxtApp.vueApp.component('Toast', Toast)

  if (import.meta.client) {
    const removeLicenseElements = () => {
      const allDivs = document.querySelectorAll('div, a, span')
      allDivs.forEach((el) => {
        const text = el.textContent || ''
        if (text.includes('Invalid PrimeUI License') || text.includes('PrimeUI License')) {
          el.remove()
        }
      })
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('DOMContentLoaded', removeLicenseElements)
      setTimeout(removeLicenseElements, 100)
      setTimeout(removeLicenseElements, 500)
      setTimeout(removeLicenseElements, 1500)

      const observer = new MutationObserver(() => {
        removeLicenseElements()
      })
      observer.observe(document.body, { childList: true, subtree: true })
    }
  }
})
