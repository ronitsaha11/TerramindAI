import { type Layer } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import { type DeckOverlayManager } from './DeckOverlayManager'
import { useLayerStore } from '../stores/useLayerStore'
import {
  type LayerId,
  type LayerConfig,
  type LayerRuntime,
  type LayerState,
} from '../types/layer.types'

interface DemoPoint {
  position: [number, number]
  radius: number
  color: [number, number, number, number]
}

const DEMO_POINTS: DemoPoint[] = [
  { position: [2.3522, 48.8566],   radius: 40000, color: [0, 188, 212, 200] },   // Paris
  { position: [-0.1278, 51.5074],  radius: 40000, color: [156, 39, 176, 200] },  // London
  { position: [13.4050, 52.5200],  radius: 40000, color: [255, 87, 34, 200] },   // Berlin
  { position: [-73.9857, 40.7484], radius: 40000, color: [76, 175, 80, 200] },   // New York
  { position: [139.6917, 35.6895], radius: 40000, color: [255, 193, 7, 200] },   // Tokyo
  { position: [-43.1729, -22.9068],radius: 40000, color: [244, 67, 54, 200] },   // Rio
  { position: [28.9784, 41.0082],  radius: 40000, color: [0, 150, 136, 200] },   // Istanbul
  { position: [72.8777, 19.0760],  radius: 40000, color: [233, 30, 99, 200] },   // Mumbai
]

/**
 * LayerManager is the canonical owner of all layer business logic.
 *
 * Data flow:
 *   registerLayer() → internal registry → syncRenderer() → DeckOverlayManager
 *                                        → syncStore() → useLayerStore → React
 */
export class LayerManager {
  private _registry = new Map<LayerId, LayerRuntime>()
  private _deckOverlay: DeckOverlayManager | null = null
  private _initialized = false

  // ─────────────────────────────────────────────
  // Lifecycle
  // ─────────────────────────────────────────────

  initialize(deckOverlay: DeckOverlayManager): void {
    if (this._initialized) return
    this._deckOverlay = deckOverlay
    this._initialized = true
  }

  destroy(): void {
    this._registry.clear()
    this._deckOverlay = null
    this._initialized = false
    useLayerStore.getState().reset()
  }

  // ─────────────────────────────────────────────
  // Layer lifecycle
  // ─────────────────────────────────────────────

  /** Register a new layer. Duplicate IDs are ignored. */
  registerLayer(config: LayerConfig): void {
    if (this._registry.has(config.id)) return

    const runtime: LayerRuntime = {
      definition: { config, createdAt: Date.now() },
      visible: config.style.visible,
      opacity: config.style.opacity,
      selected: false,
      order: this._registry.size,
    }
    this._registry.set(config.id, runtime)
    this.syncRenderer()
    this.syncStore()
  }

  /** Unregister and remove a layer from the renderer. */
  removeLayer(id: LayerId): void {
    this._registry.delete(id)
    this._reorderAfterRemoval()
    this.syncRenderer()
    this.syncStore()
  }

  /** Replace a layer's full configuration. */
  updateLayer(id: LayerId, config: Partial<LayerConfig>): void {
    const runtime = this._registry.get(id)
    if (!runtime) return
    this._registry.set(id, {
      ...runtime,
      definition: {
        ...runtime.definition,
        config: { ...runtime.definition.config, ...config },
      },
    })
    this.syncRenderer()
    this.syncStore()
  }

  /** Toggle a layer's visibility. */
  setVisibility(id: LayerId, visible: boolean): void {
    const runtime = this._registry.get(id)
    if (!runtime) return
    this._registry.set(id, { ...runtime, visible })
    this.syncRenderer()
    this.syncStore()
  }

  /** Set a layer's opacity (0–1). */
  setOpacity(id: LayerId, opacity: number): void {
    const runtime = this._registry.get(id)
    if (!runtime) return
    const clamped = Math.max(0, Math.min(1, opacity))
    this._registry.set(id, { ...runtime, opacity: clamped })
    this.syncRenderer()
    this.syncStore()
  }

  /** Reorder a layer by moving it to a new zero-based index position. */
  moveLayer(id: LayerId, toIndex: number): void {
    const ids = this._getOrderedIds()
    const fromIndex = ids.indexOf(id)
    if (fromIndex === -1 || fromIndex === toIndex) return

    ids.splice(fromIndex, 1)
    ids.splice(toIndex, 0, id)
    ids.forEach((layerId, i) => {
      const rt = this._registry.get(layerId)
      if (rt) this._registry.set(layerId, { ...rt, order: i })
    })
    this.syncRenderer()
    this.syncStore()
  }

  /** Mark a layer as selected (exclusive selection). */
  selectLayer(id: LayerId | null): void {
    for (const [layerId, rt] of this._registry) {
      this._registry.set(layerId, { ...rt, selected: layerId === id })
    }
    useLayerStore.getState().selectLayer(id)
    this.syncStore()
  }

  // ─────────────────────────────────────────────
  // Sync
  // ─────────────────────────────────────────────

  /** Push visible layers to the Deck.gl rendering backend in render order. */
  syncRenderer(): void {
    if (!this._deckOverlay) return
    const layers = this._buildDeckLayers()
    this._deckOverlay.renderLayers(layers)
  }

  /** Push a read-only snapshot of layer state to useLayerStore. */
  syncStore(): void {
    const ordered = this._getOrderedIds()
    const layerStates: LayerState[] = ordered.map((id) => {
      const rt = this._registry.get(id)!
      return {
        id,
        label: rt.definition.config.label,
        category: rt.definition.config.category,
        visible: rt.visible,
        opacity: rt.opacity,
        selected: rt.selected,
        order: rt.order,
      }
    })
    useLayerStore.getState().setLayers(layerStates, ordered)
  }

  // ─────────────────────────────────────────────
  // Static factory — demo layer
  // ─────────────────────────────────────────────

  static buildDemoLayer(id: LayerId, opacity: number): Layer {
    return new ScatterplotLayer<DemoPoint>({
      id,
      data: DEMO_POINTS,
      opacity,
      getPosition: (d: DemoPoint) => d.position,
      getRadius: (d: DemoPoint) => d.radius,
      getFillColor: (d: DemoPoint) => d.color,
      radiusUnits: 'meters',
      radiusMinPixels: 4,
      radiusMaxPixels: 40,
      pickable: false,
    })
  }

  // ─────────────────────────────────────────────
  // Private helpers
  // ─────────────────────────────────────────────

  private _getOrderedIds(): LayerId[] {
    return Array.from(this._registry.entries())
      .sort(([, a], [, b]) => a.order - b.order)
      .map(([id]) => id)
  }

  private _buildDeckLayers(): Layer[] {
    return this._getOrderedIds()
      .map((id) => this._registry.get(id)!)
      .filter((rt) => rt.visible)
      .map((rt) =>
        LayerManager.buildDemoLayer(rt.definition.config.id, rt.opacity)
      )
  }

  private _reorderAfterRemoval(): void {
    const ids = this._getOrderedIds()
    ids.forEach((id, i) => {
      const rt = this._registry.get(id)
      if (rt) this._registry.set(id, { ...rt, order: i })
    })
  }
}
