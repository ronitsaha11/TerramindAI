import { useRef } from 'react'
import { useRenderSurface } from '../hooks/useRenderSurface'

export function RenderSurface() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useRenderSurface(canvasRef)

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full block"
      aria-label="Earth Rendering Surface"
    />
  )
}
