import { useRef } from 'react'
import { useRenderSurface } from '../hooks/useRenderSurface'
import { useCameraStore } from '../stores/useCameraStore'

export function RenderSurface() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isMoving = useCameraStore((state) => state.isMoving)

  useRenderSurface(containerRef)

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 w-full h-full ${isMoving ? 'cursor-grabbing' : 'cursor-grab'}`}
      aria-label="Earth Rendering Surface"
    />
  )
}
