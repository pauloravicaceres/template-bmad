// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-10-03',
  devtools: { enabled: true },
  ssr: false,
  modules: ['@nuxtjs/tailwindcss'],
  css: ['primeicons/primeicons.css', '~/assets/css/main.css'],
  experimental: {
    appManifest: false,
  },
})
