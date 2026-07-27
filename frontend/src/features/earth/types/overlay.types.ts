import { type Layer } from '@deck.gl/core'

/** Unique string identifier for an overlay. */
export type OverlayId = string

/** Broad classification of the overlay's rendering category. */
export type OverlayCategory =
  | 'scatter'
  | 'heatmap'
  | 'geojson'
  | 'raster'
  | 'polygon'
  | 'line'
  | 'terrain'
  | 'custom'

/** Descriptive metadata attached to every overlay registration. */
export interface OverlayMetadata {
  id: OverlayId
  category: OverlayCategory
  label: string
  description?: string
  createdAt: number
}

/** A registered overlay — combines metadata with the live Deck layer. */
export interface OverlayDefinition {
  metadata: OverlayMetadata
  layer: Layer
  visible: boolean
}

/** Read-only view of an overlay's current state. */
export interface OverlayState {
  id: OverlayId
  label: string
  category: OverlayCategory
  visible: boolean
}
