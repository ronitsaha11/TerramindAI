import { EarthViewport } from '@/features/earth/components/EarthViewport'

export function MapViewport() {
  return (
    <main className="flex-1 relative overflow-hidden">
      <EarthViewport />
    </main>
  )
}
