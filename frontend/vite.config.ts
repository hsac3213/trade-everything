import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    // https://ko.vite.dev/config/server-options.html#server-allowedhosts
    // (!) server.allowedHosts를 true로 설정하면 DNS 리바인딩 공격을 통해 어떤 웹사이트에서든 개발 서버에 요청을 보낼 수 있게 됨.
    allowedHosts: true  
  }
})
