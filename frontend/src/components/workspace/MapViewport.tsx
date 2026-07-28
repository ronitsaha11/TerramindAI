import { EarthViewport } from '@/features/earth/components/EarthViewport'
import { FeatureTooltip } from '@/features/interactions/components'
import { VisibleFeaturesCounter } from '@/features/spatial/components/VisibleFeaturesCounter'

export function MapViewport() {
  return (
    <main className="flex-1 relative overflow-hidden">
      <EarthViewport />
      <VisibleFeaturesCounter />
      <FeatureTooltip />
    </main>
  )
}
