import { MapboxOverlay } from '@deck.gl/mapbox'
import { type Layer } from '@deck.gl/core'
import { type Map as MapLibreMap, type IControl } from 'maplibre-gl'

/**
 * DeckOverlayManager is a pure rendering backend.
 * It holds NO business logic. It only renders the layer list it receives.
 * All business logic lives in LayerManager.
 */
export class DeckOverlayManager {
  private _overlay: MapboxOverlay | null = null

  /** Initialize and attach the shared-context MapboxOverlay. */
  initialize(map: MapLibreMap): void {
    if (this._overlay) return
    this._overlay = new MapboxOverlay({
      interleaved: true,
      parameters: {
        depthTest: true,
        blend: true,
        blendFunc: [
          WebGLRenderingContext.SRC_ALPHA,
          WebGLRenderingContext.ONE_MINUS_SRC_ALPHA,
          WebGLRenderingContext.ONE,
          WebGLRenderingContext.ONE_MINUS_SRC_ALPHA
        ],
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      layers: [],
    })
    map.addControl(this._overlay as unknown as IControl)
  }

  /** Push an ordered list of visible layers to the Deck renderer. */
  renderLayers(layers: Layer[]): void {
    this._overlay?.setProps({ layers })
  }

  /** Remove all layers from the renderer without destroying the control. */
  clear(): void {
    this._overlay?.setProps({ layers: [] })
  }

  /** Finalize and release the WebGL context. */
  destroy(): void {
    if (this._overlay) {
      try {
        this._overlay.finalize()
      } catch {
        // Already removed — safe to ignore
      }
      this._overlay = null
    }
  }
}
