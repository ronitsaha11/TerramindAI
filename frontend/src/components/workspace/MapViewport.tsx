import { EarthViewport } from '@/features/earth/components/EarthViewport'
import { FeatureTooltip } from '@/features/interactions/components'

export function MapViewport() {
  return (
    <main className="flex-1 relative overflow-hidden">
      <EarthViewport />
      <FeatureTooltip />
    </main>
  )
}
