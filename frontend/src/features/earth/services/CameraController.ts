import { type Map as MapLibreMap, type LngLatBoundsLike } from 'maplibre-gl'
import { useCameraStore } from '../stores/useCameraStore'
import { 
  type CameraPosition,
  type FlyToOptions, 
  type JumpToOptions, 
  type FitBoundsOptions,
  type CameraBounds
} from '../types/camera.types'

export type CameraListener = (camera: CameraPosition) => void

export class CameraController {
  private _map: MapLibreMap | null = null
  private _isSyncing = false
  private _listeners = new Set<CameraListener>()

  /** Bind to a MapLibre instance. */
  bind(map: MapLibreMap): void {
    this._map = map
  }

  /** Unbind from the current renderer. */
  unbind(): void {
    this._map = null
    this._listeners.clear()
  }

  /** Register a listener that fires on every camera update. */
  subscribe(listener: CameraListener): void {
    this._listeners.add(listener)
  }

  /** Unregister a previously registered camera listener. */
  unsubscribe(listener: CameraListener): void {
    this._listeners.delete(listener)
  }

  // ─────────────────────────────────────────────
  // Synchronization from renderer → store
  // ─────────────────────────────────────────────

  /** Read current state from renderer and push to CameraStore. */
  syncFromRenderer(): void {
    if (!this._map || this._isSyncing) return
    const map = this._map

    const center = map.getCenter()
    const camera: CameraPosition = {
      longitude: center.lng,
      latitude: center.lat,
      zoom: map.getZoom(),
      pitch: map.getPitch(),
      bearing: map.getBearing(),
    }

    const { setCamera } = useCameraStore.getState()
    setCamera(camera)

    for (const listener of this._listeners) {
      listener(camera)
    }
  }

  /** Signal that the camera is actively moving. */
  setMoving(moving: boolean): void {
    useCameraStore.getState().setMoving(moving)
  }

  // ─────────────────────────────────────────────
  // Camera read
  // ─────────────────────────────────────────────

  /** Return the current camera position from the store. */
  getCamera(): CameraPosition {
    return useCameraStore.getState().camera
  }

  // ─────────────────────────────────────────────
  // Camera commands
  // ─────────────────────────────────────────────

  /** Animated flight to a position. */
  flyTo(options: FlyToOptions): void {
    if (!this._map) return
    this._isSyncing = true
    try {
      this._map.flyTo({
        center: options.center,
        zoom: options.zoom,
        pitch: options.pitch,
        bearing: options.bearing,
        duration: options.duration ?? 1200,
        curve: options.curve ?? 1.42,
      })
    } finally {
      this._isSyncing = false
    }
  }

  /** Instant camera jump to a position. */
  jumpTo(options: JumpToOptions): void {
    if (!this._map) return
    this._isSyncing = true
    try {
      this._map.jumpTo({
        center: options.center,
        zoom: options.zoom,
        pitch: options.pitch,
        bearing: options.bearing,
      })
    } finally {
      this._isSyncing = false
    }
  }

  /** Fit the viewport to a bounding box. */
  fitBounds(bounds: CameraBounds, options?: FitBoundsOptions): void {
    if (!this._map) return
    const lngLatBounds: LngLatBoundsLike = [
      [bounds.west, bounds.south],
      [bounds.east, bounds.north],
    ]
    this._map.fitBounds(lngLatBounds, {
      padding: options?.padding ?? 40,
      maxZoom: options?.maxZoom,
      duration: options?.duration ?? 800,
    })
  }

  /** Zoom in by one level. */
  zoomIn(): void {
    if (!this._map) return
    this._map.zoomIn()
  }

  /** Update map padding to accommodate workspace UI overlays. */
  syncPadding(padding: { top: number; bottom: number; left: number; right: number }): void {
    if (!this._map) return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    
    this._isSyncing = true
    try {
      this._map.easeTo({
        padding,
        duration: prefersReducedMotion ? 0 : 300,
      })
    } finally {
      this._isSyncing = false
    }
  }

  /** Zoom out by one level. */
  zoomOut(): void {
    if (!this._map) return
    this._map.zoomOut()
  }

  /** Set the map rotation in degrees. */
  rotate(bearing: number): void {
    if (!this._map) return
    this._map.rotateTo(bearing)
  }

  /** Set the pitch (tilt) angle in degrees. */
  setPitch(pitch: number): void {
    if (!this._map) return
    this._map.setPitch(pitch)
  }

  /** Reset bearing to north (0°). */
  resetNorth(): void {
    if (!this._map) return
    this._map.resetNorth()
  }

  /** 
   * Temporary terrain demonstration preset for development and testing. 
   * Provides a dramatic 3D view of Mount Everest.
   */
  flyToTerrainPreset(): void {
    this.flyTo({
      center: [86.9250, 27.9881],
      zoom: 12,
      pitch: 75,
      bearing: 45,
      duration: 3000,
    })
  }
}
