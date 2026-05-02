import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Mail Manager',
        short_name: 'MailMgr',
        description: 'Privacy-first email cleaner',
        theme_color: '#3f51b5',
        icons: [{ src: 'logo.jpg', sizes: '192x192', type: 'image/jpeg' }]
      }
    })
  ]
})
