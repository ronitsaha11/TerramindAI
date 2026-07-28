import { WorkspacePanel } from './WorkspacePanel'
import { useLayerStore } from '@/features/earth/stores/useLayerStore'
import { EarthEngine } from '@/features/earth/services/EarthEngine'
import { Eye, EyeOff, Layers } from 'lucide-react'
import { FeatureInspector } from '@/features/interactions/components'
import { DatasetManagerPanel } from '@/features/datasets/components/DatasetManagerPanel'

function LayersPanel() {
  const layers = useLayerStore(state => state.layers)
  const selectedLayer = useLayerStore(state => state.selectedLayer)

  const handleVisibilityToggle = (id: string, current: boolean) => {
    EarthEngine.getInstance().getLayerManager()?.setVisibility(id, !current)
  }

  const handleOpacityChange = (id: string, value: number) => {
    EarthEngine.getInstance().getLayerManager()?.setOpacity(id, value)
  }

  const handleSelect = (id: string) => {
    EarthEngine.getInstance().getLayerManager()?.selectLayer(
      selectedLayer === id ? null : id
    )
  }

  return (
    <WorkspacePanel id="layers" title="Layers">
      {layers.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full gap-2 text-zinc-600">
          <Layers className="h-6 w-6" />
          <p className="text-xs">No layers registered</p>
        </div>
      ) : (
        <div className="flex flex-col gap-1">
          {layers.map(layer => (
            <div
              key={layer.id}
              onClick={() => handleSelect(layer.id)}
              className={[
                'group flex flex-col gap-2 p-2 rounded-md cursor-pointer transition-colors',
                selectedLayer === layer.id
                  ? 'bg-zinc-800 border border-zinc-700'
                  : 'hover:bg-zinc-900 border border-transparent',
              ].join(' ')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={[
                      'text-xs font-medium truncate transition-colors',
                      layer.visible ? 'text-zinc-200' : 'text-zinc-600',
                    ].join(' ')}
                  >
                    {layer.label}
                  </span>
                  <span className="text-[10px] text-zinc-600 uppercase shrink-0">
                    {layer.category}
                  </span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleVisibilityToggle(layer.id, layer.visible) }}
                  className="ml-1 text-zinc-500 hover:text-zinc-200 transition-colors shrink-0"
                  aria-label={layer.visible ? 'Hide layer' : 'Show layer'}
                >
                  {layer.visible
                    ? <Eye className="h-3.5 w-3.5" />
                    : <EyeOff className="h-3.5 w-3.5" />
                  }
                </button>
              </div>

              {/* Opacity slider */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-zinc-600 w-12 shrink-0">
                  Opacity
                </span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={layer.opacity}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) => handleOpacityChange(layer.id, parseFloat(e.target.value))}
                  className="flex-1 h-1 accent-zinc-400 cursor-pointer"
                  aria-label={`Opacity for ${layer.label}`}
                />
                <span className="text-[10px] text-zinc-500 w-8 text-right shrink-0 tabular-nums">
                  {Math.round(layer.opacity * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </WorkspacePanel>
  )
}

export function DatasetsPanel() {
  return (
    <WorkspacePanel id="datasets" title="Datasets">
      <DatasetManagerPanel />
    </WorkspacePanel>
  )
}

export function WeatherPanel() {
  return <WorkspacePanel id="weather" title="Weather">Weather placeholder content</WorkspacePanel>
}
export function AIPanel() {
  return <WorkspacePanel id="ai" title="AI Assistant">AI placeholder content</WorkspacePanel>
}
export function AnalyticsPanel() {
  return <WorkspacePanel id="analytics" title="Analytics">Analytics placeholder content</WorkspacePanel>
}
export function JobsPanel() {
  return <WorkspacePanel id="jobs" title="Jobs">Jobs placeholder content</WorkspacePanel>
}
export function InspectorPanel() {
  return (
    <WorkspacePanel id="inspector" title="Inspector">
      <FeatureInspector />
    </WorkspacePanel>
  )
}
export function SettingsPanel() {
  return <WorkspacePanel id="settings" title="Settings">Settings placeholder content</WorkspacePanel>
}
export { LayersPanel }
