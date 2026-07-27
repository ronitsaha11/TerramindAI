import { Map as MapLibreMap } from 'maplibre-gl'
import { useMapStore } from '../stores/useMapStore'
import { CameraController } from './CameraController'
import { type FlyToOptions, type JumpToOptions, type FitBoundsOptions, type CameraBounds } from '../types/camera.types'

export type EngineState = 'uninitialized' | 'mounting' | 'ready' | 'error' | 'destroyed'

export class EarthEngine {
  private static instance: EarthEngine | null = null

  private _state: EngineState = 'uninitialized'
  private _hostElement: HTMLElement | null = null
  private _map: MapLibreMap | null = null
  private _camera: CameraController | null = null
  // Reserved for future Deck.gl integration — placeholder until Phase 11.4
  private declare _deck: unknown

  static getInstance(): EarthEngine {
    if (!EarthEngine.instance) {
      EarthEngine.instance = new EarthEngine()
    }
    return EarthEngine.instance
  }

  get state(): EngineState {
    return this._state
  }

  private setState(state: EngineState): void {
    this._state = state
    const { setEngineState, setEngineReady } = useMapStore.getState()
    setEngineState(state)
    setEngineReady(state === 'ready')
  }

  /** Attach to a host DOM element. */
  attach(element: HTMLElement): void {
    if (this._state === 'destroyed') {
      console.warn('[EarthEngine] Cannot attach — engine is destroyed.')
      return
    }
    if (this._hostElement === element) return
    if (this._hostElement) {
      this.detach()
    }
    this._hostElement = element
  }

  detach(): void {
    this._hostElement = null
  }

  /** Initialize the engine. Idempotent — duplicate calls are ignored. */
  initialize(): void {
    if (this._state === 'ready' || this._state === 'mounting') return
    if (this._state === 'destroyed' || this._state === 'error') {
      console.warn(`[EarthEngine] Cannot initialize — engine is in "${this._state}" state.`)
      return
    }
    if (!this._hostElement) {
      console.error('[EarthEngine] Cannot initialize — no host element attached.')
      return
    }

    this.setState('mounting')

    try {
      const map = new MapLibreMap({
        container: this._hostElement,
        style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        center: [0, 20],
        zoom: 2,
        pitch: 0,
        bearing: 0,
        attributionControl: {},
      })

      this._map = map

      // Instantiate and bind CameraController
      const camera = new CameraController()
      this._camera = camera

      map.once('load', () => {
        if (this._state !== 'mounting') return

        // Bind camera to the now-ready renderer
        camera.bind(map)
        camera.syncFromRenderer()

        // Forward renderer camera events → CameraController
        const syncEvents = ['move', 'zoom', 'rotate', 'pitch'] as const
        for (const evt of syncEvents) {
          map.on(evt, () => camera.syncFromRenderer())
        }

        map.on('movestart', () => camera.setMoving(true))
        map.on('moveend', () => {
          camera.syncFromRenderer()
          camera.setMoving(false)
        })

        this.setState('ready')
      })

      map.on('error', (e) => {
        console.error('[EarthEngine] MapLibre error:', e.error)
        if (this._state === 'ready' || this._state === 'mounting') {
          this.setState('error')
        }
      })
    } catch (err) {
      console.error('[EarthEngine] Failed to create MapLibre map:', err)
      this.setState('error')
    }
  }

  // ─────────────────────────────────────────────
  // Public Camera API — React calls these only
  // ─────────────────────────────────────────────

  flyTo(options: FlyToOptions): void {
    this._camera?.flyTo(options)
  }

  jumpTo(options: JumpToOptions): void {
    this._camera?.jumpTo(options)
  }

  fitBounds(bounds: CameraBounds, options?: FitBoundsOptions): void {
    this._camera?.fitBounds(bounds, options)
  }

  // ─────────────────────────────────────────────
  // Resize & Destroy
  // ─────────────────────────────────────────────

  resize(width: number, height: number): void {
    if (!this._map) return
    void width
    void height
    this._map.resize()
  }

  destroy(): void {
    if (this._state === 'destroyed') return

    this._camera?.unbind()
    this._camera = null

    if (this._map) {
      try {
        this._map.remove()
      } catch (err) {
        console.warn('[EarthEngine] Error during map removal:', err)
      }
      this._map = null
    }

    this.detach()
    this.setState('destroyed')
    EarthEngine.instance = null
  }
}
