import { Map as MapLibreMap } from 'maplibre-gl'
import { useMapStore } from '../stores/useMapStore'
import { useCursorStore } from '../stores/useCursorStore'
import { CameraController } from './CameraController'
import { CoordinateService } from './CoordinateService'
import { ProjectionService } from './ProjectionService'
import { DeckOverlayManager } from './DeckOverlayManager'
import { type FlyToOptions, type JumpToOptions, type FitBoundsOptions, type CameraBounds } from '../types/camera.types'

export type EngineState = 'uninitialized' | 'mounting' | 'ready' | 'error' | 'destroyed'

export class EarthEngine {
  private static instance: EarthEngine | null = null

  private _state: EngineState = 'uninitialized'
  private _hostElement: HTMLElement | null = null
  private _map: MapLibreMap | null = null
  private _camera: CameraController | null = null
  private _projection: ProjectionService | null = null
  private _deckOverlayManager: DeckOverlayManager | null = null
  // Reserved for future additional renderers — placeholder
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

  attach(element: HTMLElement): void {
    if (this._state === 'destroyed') {
      console.warn('[EarthEngine] Cannot attach — engine is destroyed.')
      return
    }
    if (this._hostElement === element) return
    if (this._hostElement) this.detach()
    this._hostElement = element
  }

  detach(): void {
    this._hostElement = null
  }

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

      // Instantiate services
      const camera = new CameraController()
      const coordinates = new CoordinateService()
      const projection = new ProjectionService()

      this._camera = camera
      this._projection = projection

      map.once('load', () => {
        if (this._state !== 'mounting') return

        // Bind services to the live renderer
        camera.bind(map)
        projection.bind(map)
        camera.syncFromRenderer()

        // ─── Camera events ───────────────────────────
        const syncEvents = ['move', 'zoom', 'rotate', 'pitch'] as const
        for (const evt of syncEvents) {
          map.on(evt, () => camera.syncFromRenderer())
        }
        map.on('movestart', () => camera.setMoving(true))
        map.on('moveend', () => {
          camera.syncFromRenderer()
          camera.setMoving(false)
        })

        // ─── Cursor events ───────────────────────────
        const { setCursor, clearCursor } = useCursorStore.getState()

        map.on('mousemove', (e) => {
          const coord = coordinates.unproject(map, { x: e.point.x, y: e.point.y })
          if (coord) {
            setCursor({ ...coord, x: e.point.x, y: e.point.y })
          }
        })

        map.on('mouseout', () => {
          clearCursor()
        })

        // ─── Deck.gl overlay pipeline ──────────────
        const deckManager = new DeckOverlayManager()
        this._deckOverlayManager = deckManager
        deckManager.initialize(map)

        // Register the demonstration ScatterplotLayer through the registry
        deckManager.addOverlay(
          'demo-cities',
          DeckOverlayManager.buildDemoLayer(),
          { category: 'scatter', label: 'Demo Cities' },
        )

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
  // Public Camera API
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

  /** Access the overlay manager. React components must never access Deck.gl directly. */
  getOverlayManager(): DeckOverlayManager | null {
    return this._deckOverlayManager
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

    this._projection?.unbind()
    this._projection = null

    this._deckOverlayManager?.destroy()
    this._deckOverlayManager = null

    useCursorStore.getState().clearCursor()

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
