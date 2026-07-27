import { RenderSurface } from './RenderSurface'
import { EngineLoader } from './EngineLoader'

export function EarthViewport() {
  return (
    <div className="absolute inset-0 overflow-hidden bg-zinc-950">
      <RenderSurface />
      <EngineLoader />
    </div>
  )
}
