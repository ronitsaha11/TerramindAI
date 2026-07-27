import { useEffect, useRef } from 'react'
import { EarthEngine } from '../services/EarthEngine'

export function useRenderSurface(canvasRef: React.RefObject<HTMLCanvasElement | null>) {
  const engineRef = useRef<EarthEngine | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const engine = EarthEngine.getInstance()
    engineRef.current = engine

    engine.attach(canvas)
    engine.initialize()

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        engine.resize(width, height)
      }
    })
    observer.observe(canvas)

    return () => {
      observer.disconnect()
      engine.destroy()
      engineRef.current = null
    }
  }, [canvasRef])
}
