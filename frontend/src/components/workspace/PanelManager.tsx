import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { 
  LayersPanel, 
  DatasetsPanel,
  WeatherPanel, 
  AIPanel, 
  AnalyticsPanel, 
  JobsPanel, 
  InspectorPanel,
  SettingsPanel
} from './panels'
import { type ComponentType } from 'react'
import { AnimatePresence } from 'framer-motion'

const panelRegistry: Record<string, ComponentType> = {
  layers: LayersPanel,
  datasets: DatasetsPanel,
  weather: WeatherPanel,
  ai: AIPanel,
  analytics: AnalyticsPanel,
  jobs: JobsPanel,
  inspector: InspectorPanel,
  settings: SettingsPanel,
}

export function PanelManager() {
  const activePanels = useWorkspaceStore(state => state.activePanels)

  return (
    <div className="absolute inset-0 p-4 flex gap-4 flex-wrap items-start justify-start pointer-events-none z-10">
      <AnimatePresence mode="popLayout">
        {activePanels.map(id => {
          const PanelComponent = panelRegistry[id]
          if (!PanelComponent) return null
          return <PanelComponent key={id} />
        })}
      </AnimatePresence>
    </div>
  )
}

