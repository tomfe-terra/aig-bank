import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

function validateEnv(env: Record<string, string>) {
  if (!env.VITE_API_BASE_URL) {
    return
  }

  try {
    const url = new URL(env.VITE_API_BASE_URL)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      throw new Error('Invalid protocol')
    }
  } catch {
    throw new Error(
      `❌ VITE_API_BASE_URL has invalid format: ${env.VITE_API_BASE_URL}\n` +
      `   Expected: http(s)://host:port/api/v1`
    )
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  validateEnv(env)
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: env.VITE_HOST || 'localhost',
      port: parseInt(env.VITE_PORT || '3000')
    }
  }
})

