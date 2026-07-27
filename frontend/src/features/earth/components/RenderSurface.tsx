import { useRef } from 'react'
import { useRenderSurface } from '../hooks/useRenderSurface'

export function RenderSurface() {
  const containerRef = useRef<HTMLDivElement>(null)

  useRenderSurface(containerRef)

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full"
      aria-label="Earth Rendering Surface"
    />
  )
}
