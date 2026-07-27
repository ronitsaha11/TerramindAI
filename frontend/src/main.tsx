import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppProviders } from '@/providers/AppProviders'
import App from './App.tsx'
import './styles/globals.css'
import 'maplibre-gl/dist/maplibre-gl.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
)
