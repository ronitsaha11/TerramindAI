import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppProviders } from '@/providers/AppProviders'
import App from './App.tsx'
import './styles/globals.css'
import 'maplibre-gl/dist/maplibre-gl.css'
import { EarthEngine } from './features/earth/services/EarthEngine'
import { useWorkspaceStore } from './stores/workspace/useWorkspaceStore'

// Exposed for debugging from the browser console, e.g.
//   window.EarthEngine.getInstance().getMap()
declare global {
  interface Window {
    EarthEngine: typeof EarthEngine
    useWorkspaceStore: typeof useWorkspaceStore
  }
}

window.EarthEngine = EarthEngine
window.useWorkspaceStore = useWorkspaceStore

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
)
