import { useMapStore } from '../stores/useMapStore'

export type EngineState = 'uninitialized' | 'mounting' | 'ready' | 'destroyed'

export class EarthEngine {
  private static instance: EarthEngine | null = null

  private _state: EngineState = 'uninitialized'
  private _canvas: HTMLCanvasElement | null = null
  private _resizeObserver: ResizeObserver | null = null

  // Singleton accessor — ensures a single engine across the app lifetime
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

  /** Attach to a canvas DOM element. No-op if already attached. */
  attach(canvas: HTMLCanvasElement): void {
    if (this._state === 'destroyed') {
      console.warn('[EarthEngine] Cannot attach — engine is destroyed.')
      return
    }
    if (this._canvas === canvas) return
    if (this._canvas) {
      this.detach()
    }
    this._canvas = canvas
  }

  /** Detach from the current canvas. */
  detach(): void {
    this._canvas = null
  }

  /** Initialize the engine. Idempotent — safe to call multiple times. */
  initialize(): void {
    if (this._state === 'ready' || this._state === 'mounting') {
      return
    }
    if (this._state === 'destroyed') {
      console.warn('[EarthEngine] Cannot initialize — engine is destroyed.')
      return
    }

    this.setState('mounting')

    // Stub: engine initialization sequence
    // In future sprints, MapLibre / Deck.gl / Three.js will be attached here.
    // For now, transition to ready on the next microtask.
    Promise.resolve().then(() => {
      if (this._state !== 'mounting') return
      this.setState('ready')
    })
  }

  /** Forward a resize event to the renderer. */
  resize(width: number, height: number): void {
    if (this._state !== 'ready') return
    // Future: renderer.resize(width, height)
    void width
    void height
  }

  /** Tear down the engine and release all resources. */
  destroy(): void {
    if (this._state === 'destroyed') return
    this._resizeObserver?.disconnect()
    this._resizeObserver = null
    this.detach()
    this.setState('destroyed')
    EarthEngine.instance = null
  }
}
