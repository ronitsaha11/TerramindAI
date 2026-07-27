import { useEffect, useRef } from 'react'
import { EarthEngine } from '../services/EarthEngine'

export function useRenderSurface(containerRef: React.RefObject<HTMLDivElement | null>) {
  const engineRef = useRef<EarthEngine | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const engine = EarthEngine.getInstance()
    engineRef.current = engine

    engine.attach(container)
    engine.initialize()

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        engine.resize(width, height)
      }
    })
    observer.observe(container)

    return () => {
      observer.disconnect()
      engine.destroy()
      engineRef.current = null
    }
  }, [containerRef])
}
