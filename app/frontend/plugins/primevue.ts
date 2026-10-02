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
})
