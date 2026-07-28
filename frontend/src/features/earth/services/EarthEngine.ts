import { Map as MapLibreMap } from 'maplibre-gl'
import { useMapStore } from '../stores/useMapStore'
import { useCursorStore } from '../stores/useCursorStore'
import { useWorkspaceStatusStore } from '@/stores/workspace/useWorkspaceStatusStore'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { useEnvironmentStore } from '../stores/useEnvironmentStore'
import { CameraController } from './CameraController'
import { CoordinateService } from './CoordinateService'
import { ProjectionService } from './ProjectionService'
import { DeckOverlayManager } from './DeckOverlayManager'
import { LayerManager } from './LayerManager'
import { FPSTracker } from './FPSTracker'
import { InteractionManager } from '../../../core/interactions/interaction-manager'
import { DeckInteractionAdapter } from '../adapters/deck-interaction-adapter'
import { InteractionBridge } from '../stores/interaction-bridge'
import { StyleEvaluator } from '../../../core/styles/style-evaluator'
import { DatasetLayerFactory } from '../../../core/datasets/rendering/dataset-layer.factory'
import { SpatialEngine } from '../../../core/spatial/spatial.engine'
import { DatasetRegistry } from '../../../core/datasets/registry/dataset-registry'
import { ViewportQueryController } from './viewport-query-controller'
import { SpatialBridge } from '../../spatial/stores/spatial-bridge'
import { EnvironmentController } from './EnvironmentController'
import { type FlyToOptions, type JumpToOptions, type FitBoundsOptions, type CameraBounds } from '../types/camera.types'
import { SimulationClock } from '../../../core/simulation'
import { SimulationBridge } from '../../simulation/stores/simulation-bridge'

export type EngineState = 'uninitialized' | 'mounting' | 'ready' | 'error' | 'destroyed'

export class EarthEngine {
  private static instance: EarthEngine | null = null

  private _state: EngineState = 'uninitialized'
  private _hostElement: HTMLElement | null = null
  private _map: MapLibreMap | null = null
  private _camera: CameraController | null = null
  private _projection: ProjectionService | null = null
  private _coordinates: CoordinateService | null = null
  private _deckOverlayManager: DeckOverlayManager | null = null
  private _layerManager: LayerManager | null = null
  private _interactionBridge: InteractionBridge | null = null
  private _datasetLayerFactory: DatasetLayerFactory | null = null
  private _viewportQueryController: ViewportQueryController | null = null
  private _spatialBridge: SpatialBridge | null = null
  private _datasetRegistry: DatasetRegistry | null = null
  private _fpsTracker: FPSTracker | null = null
  private _environmentController: EnvironmentController | null = null
  private _simulationClock: SimulationClock | null = null
  private _simulationBridge: SimulationBridge | null = null
  private _unsubWorkspace: (() => void) | null = null
  private _unsubEnvironment: (() => void) | null = null
  private _animationFrameId: number | null = null
  private _lastFrameTime: number | null = null

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
    if (this._state === 'ready' || this._state === 'mounting') {
      return
    }
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

      const camera = new CameraController()
      const coordinates = new CoordinateService()
      const projection = new ProjectionService()
      const fpsTracker = new FPSTracker()
      const environmentController = new EnvironmentController()
      
      const simulationClock = new SimulationClock()
      const simulationBridge = new SimulationBridge(simulationClock)
      simulationBridge.initialize()

      this._camera = camera
      this._projection = projection
      this._coordinates = coordinates
      this._fpsTracker = fpsTracker
      this._environmentController = environmentController
      this._simulationClock = simulationClock
      this._simulationBridge = simulationBridge

      map.once('load', () => {
        if (this._state !== 'mounting') return

        // ─── Bind services ──────────────────────────
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
          coordinates.throttleCursorUpdate(map, e, setCursor)
        })
        map.on('mouseout', () => {
          coordinates.clearThrottle()
          clearCursor()
        })

        // ─── FPS Tracking ────────────────────────────
        fpsTracker.subscribe((fps) => {
          useWorkspaceStatusStore.getState().setFPS(fps)
        })
        fpsTracker.start()

        // ─── Workspace Padding ───────────────────────
        const updatePadding = () => {
          const { leftSidebarOpen, rightSidebarOpen } = useWorkspaceStore.getState()
          camera.syncPadding({
            top: 48,
            bottom: 28,
            left: leftSidebarOpen ? 256 : 48,
            right: rightSidebarOpen ? 256 : 48,
          })
        }
        updatePadding()
        this._unsubWorkspace = useWorkspaceStore.subscribe(
          (state, prevState) => {
            if (state.leftSidebarOpen !== prevState.leftSidebarOpen ||
                state.rightSidebarOpen !== prevState.rightSidebarOpen) {
              updatePadding()
            }
          }
        )

        // ─── Deck.gl & Layer Manager ─────────────────
        const deckManager = new DeckOverlayManager()
        deckManager.initialize(map)
        this._deckOverlayManager = deckManager

        const interactionManager = new InteractionManager()
        const deckInteractionAdapter = new DeckInteractionAdapter(interactionManager)

        const interactionBridge = new InteractionBridge(interactionManager)
        interactionBridge.initialize()
        this._interactionBridge = interactionBridge

        const layerManager = new LayerManager(deckInteractionAdapter)
        layerManager.initialize(deckManager)
        this._layerManager = layerManager

        const styleEvaluator = new StyleEvaluator()
        const datasetLayerFactory = new DatasetLayerFactory(styleEvaluator)
        this._datasetLayerFactory = datasetLayerFactory

        const datasetRegistry = new DatasetRegistry()
        this._datasetRegistry = datasetRegistry

        const spatialEngine = new SpatialEngine()
        const viewportQueryController = new ViewportQueryController(spatialEngine, datasetRegistry)
        viewportQueryController.bind(map)
        this._viewportQueryController = viewportQueryController

        const spatialBridge = new SpatialBridge(viewportQueryController)
        spatialBridge.initialize()
        this._spatialBridge = spatialBridge

        // ─── Environment (Terrain/Sky) ────────────────
        environmentController.initialize(map)
        
        // Initial environment sync
        environmentController.sync(useEnvironmentStore.getState())
        
        // Subscribe to environment store
        this._unsubEnvironment = useEnvironmentStore.subscribe((state) => {
          environmentController.sync(state)
        })

        // ─── Simulation Loop ─────────────────────────
        this._lastFrameTime = performance.now()
        const loop = (currentTime: number) => {
          if (this._state === 'destroyed') return;
          
          if (this._lastFrameTime !== null) {
            const realWorldDeltaMs = currentTime - this._lastFrameTime;
            this._simulationClock?.tick(realWorldDeltaMs);
          }
          this._lastFrameTime = currentTime;
          
          this._animationFrameId = requestAnimationFrame(loop);
        }
        this._animationFrameId = requestAnimationFrame(loop);

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

  // ─────────────────────────────────────────────
  // Public Layer API
  // ─────────────────────────────────────────────

  /** 
   * Expose the LayerManager for system-level orchestration only.
   * React components must call this through services, never directly.
   */
  getLayerManager(): LayerManager | null {
    return this._layerManager
  }

  getDatasetLayerFactory(): DatasetLayerFactory | null {
    return this._datasetLayerFactory
  }

  getViewportQueryController(): ViewportQueryController | null {
    return this._viewportQueryController
  }

  getDatasetRegistry(): DatasetRegistry | null {
    return this._datasetRegistry
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

    if (this._unsubWorkspace) {
      this._unsubWorkspace()
      this._unsubWorkspace = null
    }

    if (this._unsubEnvironment) {
      this._unsubEnvironment()
      this._unsubEnvironment = null
    }

    if (this._animationFrameId !== null) {
      cancelAnimationFrame(this._animationFrameId)
      this._animationFrameId = null
    }

    this._simulationBridge?.destroy()
    this._simulationBridge = null
    this._simulationClock = null

    this._fpsTracker?.stop()
    this._fpsTracker = null

    this._camera?.unbind()
    this._camera = null

    this._projection?.unbind()
    this._projection = null

    this._coordinates?.clearThrottle()
    this._coordinates = null

    this._layerManager?.destroy()
    this._layerManager = null

    this._interactionBridge?.destroy()
    this._interactionBridge = null

    this._spatialBridge?.destroy()
    this._spatialBridge = null

    this._environmentController?.destroy()
    this._environmentController = null

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
