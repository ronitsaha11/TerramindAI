import { MapboxOverlay } from '@deck.gl/mapbox'
import { type Layer } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import { type Map as MapLibreMap, type IControl } from 'maplibre-gl'
import {
  type OverlayId,
  type OverlayDefinition,
  type OverlayState,
  type OverlayMetadata,
} from '../types/overlay.types'

interface DemoPoint {
  position: [number, number]
  radius: number
  color: [number, number, number, number]
}

const DEMO_POINTS: DemoPoint[] = [
  { position: [2.3522, 48.8566],  radius: 40000, color: [0, 188, 212, 200] },   // Paris
  { position: [-0.1278, 51.5074], radius: 40000, color: [156, 39, 176, 200] },  // London
  { position: [13.4050, 52.5200], radius: 40000, color: [255, 87, 34, 200] },   // Berlin
  { position: [-73.9857, 40.7484],radius: 40000, color: [76, 175, 80, 200] },   // New York
  { position: [139.6917, 35.6895],radius: 40000, color: [255, 193, 7, 200] },   // Tokyo
  { position: [-43.1729, -22.9068],radius: 40000, color: [244, 67, 54, 200] },  // Rio
  { position: [28.9784, 41.0082], radius: 40000, color: [0, 150, 136, 200] },   // Istanbul
  { position: [72.8777, 19.0760], radius: 40000, color: [233, 30, 99, 200] },   // Mumbai
]

export class DeckOverlayManager {
  private _overlay: MapboxOverlay | null = null
  private _registry = new Map<OverlayId, OverlayDefinition>()

  /** Initialize MapboxOverlay and attach it to the MapLibre instance. */
  initialize(map: MapLibreMap): void {
    if (this._overlay) return

    this._overlay = new MapboxOverlay({ interleaved: true, layers: [] })
    map.addControl(this._overlay as unknown as IControl)
  }

  /** Tear down and remove the overlay from the map. */
  destroy(): void {
    this._registry.clear()
    if (this._overlay) {
      try {
        this._overlay.finalize()
      } catch {
        // Already removed
      }
      this._overlay = null
    }
  }

  /** Add a new overlay to the registry and sync to the renderer. */
  addOverlay(
    id: OverlayId,
    layer: Layer,
    meta: Omit<OverlayMetadata, 'id' | 'createdAt'>,
  ): void {
    const definition: OverlayDefinition = {
      metadata: { ...meta, id, createdAt: Date.now() },
      layer,
      visible: true,
    }
    this._registry.set(id, definition)
    this._syncLayers()
  }

  /** Replace an existing overlay's layer instance. */
  updateOverlay(id: OverlayId, layer: Layer): void {
    const definition = this._registry.get(id)
    if (!definition) return
    this._registry.set(id, { ...definition, layer })
    this._syncLayers()
  }

  /** Remove an overlay from the registry and the renderer. */
  removeOverlay(id: OverlayId): void {
    this._registry.delete(id)
    this._syncLayers()
  }

  /** Toggle visibility of a registered overlay. */
  setVisibility(id: OverlayId, visible: boolean): void {
    const definition = this._registry.get(id)
    if (!definition) return
    this._registry.set(id, { ...definition, visible })
    this._syncLayers()
  }

  /** Remove all registered overlays. */
  clear(): void {
    this._registry.clear()
    this._syncLayers()
  }

  /** Retrieve a single overlay definition. */
  getOverlay(id: OverlayId): OverlayDefinition | undefined {
    return this._registry.get(id)
  }

  /** Retrieve read-only state for all registered overlays. */
  getAll(): OverlayState[] {
    return Array.from(this._registry.values()).map((def) => ({
      id: def.metadata.id,
      label: def.metadata.label,
      category: def.metadata.category,
      visible: def.visible,
    }))
  }

  // ─────────────────────────────────────────────
  // Private
  // ─────────────────────────────────────────────

  /** Rebuild the Deck.gl layer list from the registry. */
  private _syncLayers(): void {
    if (!this._overlay) return
    const activeLayers = Array.from(this._registry.values())
      .filter((def) => def.visible)
      .map((def) => def.layer)
    this._overlay.setProps({ layers: activeLayers })
  }

  /** Build and return the demonstration ScatterplotLayer. */
  static buildDemoLayer(): Layer {
    return new ScatterplotLayer<DemoPoint>({
      id: 'demo-cities-scatter',
      data: DEMO_POINTS,
      getPosition: (d: DemoPoint) => d.position,
      getRadius: (d: DemoPoint) => d.radius,
      getFillColor: (d: DemoPoint) => d.color,
      radiusUnits: 'meters',
      radiusMinPixels: 4,
      radiusMaxPixels: 40,
      pickable: false,
    })
  }
}
