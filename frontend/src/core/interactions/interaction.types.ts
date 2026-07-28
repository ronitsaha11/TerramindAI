/**
 * Represents a discrete geospatial feature in the interaction domain.
 * This is an immutable domain object, completely decoupled from Deck.gl or MapLibre.
 */
export interface IFeature {
  /** Unique identifier of the feature, if available. */
  readonly id: string;

  /** The ID of the dataset this feature belongs to. */
  readonly datasetId: string;

  /** Key-value properties of the feature (e.g., metadata, attributes). */
  readonly properties: Readonly<Record<string, unknown>>;

  /** 
   * The underlying geometry payload. 
   * Left as unknown to maintain renderer independence. 
   */
  readonly geometry?: unknown;
}

/**
 * Immutable snapshot of the current interaction state.
 */
export interface InteractionState {
  /** The currently hovered feature, or null if nothing is hovered. */
  readonly hoveredFeature: IFeature | null;

  /** The currently selected feature, or null if nothing is selected. */
  readonly selectedFeature: IFeature | null;

  /** The X pixel coordinate of the cursor in the viewport, or null if unknown. */
  readonly cursorX: number | null;

  /** The Y pixel coordinate of the cursor in the viewport, or null if unknown. */
  readonly cursorY: number | null;
}

/**
 * A callback function that receives immutable snapshots of the interaction state
 * whenever it changes.
 */
export type InteractionChangeListener = (state: Readonly<InteractionState>) => void;
