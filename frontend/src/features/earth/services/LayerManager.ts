import { type Layer } from '@deck.gl/core'
import { GeoJsonLayer, type GeoJsonLayerProps } from '@deck.gl/layers'
import { type DeckOverlayManager } from './DeckOverlayManager'
import { useLayerStore } from '../stores/useLayerStore'
import {
  type LayerId,
  type LayerConfig,
  type LayerRuntime,
  type LayerState,
} from '../types/layer.types'


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
  private _renderDirty = false

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
      dirty: true,
    }
    this._registry.set(config.id, runtime)
    this._renderDirty = true
    this.syncRenderer()
    this.syncStore()
  }

  /** Unregister and remove a layer from the renderer. */
  removeLayer(id: LayerId): void {
    this._registry.delete(id)
    this._renderDirty = true
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
      dirty: true,
    })
    this._renderDirty = true
    this.syncRenderer()
    this.syncStore()
  }

  /** Toggle a layer's visibility. */
  setVisibility(id: LayerId, visible: boolean): void {
    const runtime = this._registry.get(id)
    if (!runtime) return
    if (runtime.visible === visible) return
    this._registry.set(id, { ...runtime, visible })
    this._renderDirty = true
    this.syncRenderer()
    this.syncStore()
  }

  /** Set a layer's opacity (0–1). */
  setOpacity(id: LayerId, opacity: number): void {
    const runtime = this._registry.get(id)
    if (!runtime) return
    const clamped = Math.max(0, Math.min(1, opacity))
    if (runtime.opacity === clamped) return
    this._registry.set(id, { ...runtime, opacity: clamped, dirty: true })
    this._renderDirty = true
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
      if (rt && rt.order !== i) this._registry.set(layerId, { ...rt, order: i })
    })
    this._renderDirty = true
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
    if (!this._deckOverlay || !this._renderDirty) return
    const layers = this._buildDeckLayers()
    this._deckOverlay.renderLayers(layers)
    this._renderDirty = false
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
  // Private Layer Builders
  // ─────────────────────────────────────────────

  private buildDeckLayer(rt: LayerRuntime): Layer | null {
    const config = rt.definition.config
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    
    if (config.category === 'geojson') {
      return new GeoJsonLayer({
        id: config.id,
        data: config.data as GeoJsonLayerProps['data'],
        opacity: rt.opacity,
        pickable: true,
        stroked: true,
        filled: true,
        lineWidthMinPixels: 1,
        getFillColor: [6, 182, 212, 150],
        getLineColor: [6, 182, 212, 255],
        transitions: prefersReducedMotion ? undefined : {
          opacity: 300,
        },
      })
    }

    console.warn(`LayerManager: Unsupported layer category '${config.category}' for layer '${config.id}'`)
    return null
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
      .map((rt) => {
        if (!rt.deckLayer || rt.dirty) {
          const layer = this.buildDeckLayer(rt)
          if (layer) {
            rt.deckLayer = layer
          }
          rt.dirty = false
        }
        return rt.deckLayer as Layer | null
      })
      .filter((layer): layer is Layer => layer !== null)
  }

  private _reorderAfterRemoval(): void {
    const ids = this._getOrderedIds()
    ids.forEach((id, i) => {
      const rt = this._registry.get(id)
      if (rt) this._registry.set(id, { ...rt, order: i })
    })
  }
}
