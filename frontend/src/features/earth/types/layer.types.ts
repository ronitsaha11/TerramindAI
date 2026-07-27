import { type Layer } from '@deck.gl/core'

/** Unique string identifier for a layer. */
export type LayerId = string

/** Broad classification determining what kind of data/rendering the layer represents. */
export type LayerCategory =
  | 'basemap'
  | 'scatter'
  | 'geojson'
  | 'raster'
  | 'heatmap'
  | 'ai'
  | 'weather'
  | 'terrain'
  | 'drawing'
  | 'measurement'
  | 'custom'

/** Visual style properties that can be applied to a layer. */
export interface LayerStyle {
  opacity: number          // 0–1
  visible: boolean
  color?: [number, number, number, number]  // RGBA
  radius?: number
  strokeWidth?: number
}

/** Static configuration provided at registration time. */
export interface LayerConfig {
  id: LayerId
  label: string
  category: LayerCategory
  style: LayerStyle
  group?: string
  description?: string
}

/** Logical grouping of layers for UI organization. */
export interface LayerGroup {
  id: string
  label: string
  collapsed: boolean
  layerIds: LayerId[]
}

/** Full layer definition combining config with optional group membership. */
export interface LayerDefinition {
  config: LayerConfig
  groupId?: string
  createdAt: number
}

/** 
 * Live runtime state of a layer — includes config plus mutable rendering state.
 * LayerManager owns this; LayerStore mirrors it.
 */
export interface LayerRuntime {
  definition: LayerDefinition
  visible: boolean
  opacity: number
  selected: boolean
  /** Render order index — lower numbers render first (beneath). */
  order: number
  /** Cached Deck.gl layer instance. */
  deckLayer?: Layer
  /** Flag indicating the layer needs to be rebuilt. */
  dirty?: boolean
}

/** Minimal read-only snapshot exposed to React via useLayerStore. */
export interface LayerState {
  id: LayerId
  label: string
  category: LayerCategory
  visible: boolean
  opacity: number
  selected: boolean
  order: number
}
