import type { IFeature } from '../interactions/interaction.types';
import type { BoundingBox, RadiusQuery, SpatialQueryResult } from './spatial.types';

/**
 * Core domain service responsible for executing geometric queries.
 * 
 * It is completely pure, stateless, and knows nothing about rendering
 * engines, viewport bounds, or application state.
 */
export interface ISpatialQueryEngine {
  /**
   * Finds all features within a specified distance from a center point.
   * 
   * @param features - The collection of features to search against.
   * @param query - The center point and radius in kilometers.
   * @returns An immutable query result containing the matching features.
   */
  findInRadius(features: ReadonlyArray<IFeature>, query: RadiusQuery): SpatialQueryResult;

  /**
   * Finds all features that intersect a specified bounding box.
   * 
   * @param features - The collection of features to search against.
   * @param bbox - The bounding box [minLng, minLat, maxLng, maxLat].
   * @returns An immutable query result containing the matching features.
   */
  findInBoundingBox(features: ReadonlyArray<IFeature>, bbox: BoundingBox): SpatialQueryResult;
}
