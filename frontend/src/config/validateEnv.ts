export function validateEnv() {
  const requiredVars = [
    'VITE_API_BASE_URL',
  ]

  const isDev = import.meta.env.DEV

  for (const envVar of requiredVars) {
    if (!import.meta.env[envVar]) {
      if (isDev) {
        console.warn(`[TerraMind Env] Missing environment variable: ${envVar}`)
      } else {
        throw new Error(`[TerraMind Env] CRITICAL: Missing environment variable: ${envVar}`)
      }
    }
  }
}
