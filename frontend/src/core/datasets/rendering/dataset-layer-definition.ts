import type { DatasetType } from '../types/dataset-type';

/**
 * Renderer-independent definition of a dataset layer.
 * This immutable object bridges the pure Dataset domain and the Rendering engines
 * without importing rendering libraries like Deck.gl or MapLibre.
 */
export interface DatasetLayerDefinition {
  /** Unique identifier for the layer. */
  readonly id: string;

  /** The ID of the dataset this layer represents. */
  readonly datasetId: string;

  /** Human-readable name for the layer. */
  readonly name: string;

  /** Original dataset format (e.g., geojson). */
  readonly datasetType: DatasetType;

  /** Type of rendering required (e.g., geojson, raster, vector-tile). */
  readonly renderType: string;

  /** Whether the layer is visible. */
  readonly visible: boolean;

  /** Opacity of the layer (0 to 1). */
  readonly opacity: number;

  /** The underlying data or data URL for the renderer to consume. */
  readonly sourceData: unknown;

  /** Renderer-agnostic styling definition. */
  readonly style: Readonly<Record<string, unknown>>;

  /** Additional metadata required for rendering. */
  readonly metadata: Readonly<Record<string, unknown>>;
}
