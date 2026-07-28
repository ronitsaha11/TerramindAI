import type { IFeature } from '../interactions/interaction.types';

/**
 * Represents a geographic bounding box.
 * Format: [minLng, minLat, maxLng, maxLat]
 */
export type BoundingBox = readonly [number, number, number, number];

/**
 * Parameters for executing a radius-based spatial search.
 */
export interface RadiusQuery {
  /** The origin point [longitude, latitude]. */
  readonly center: readonly [number, number];
  
  /** The radius in kilometers. */
  readonly radiusKm: number;
}

/**
 * The immutable result of a spatial query.
 */
export interface SpatialQueryResult {
  /** The features that matched the spatial query. */
  readonly features: ReadonlyArray<IFeature>;
  
  /** The number of matching features. */
  readonly count: number;
  
  /** The execution time of the query in milliseconds. */
  readonly elapsedMs: number;
}
