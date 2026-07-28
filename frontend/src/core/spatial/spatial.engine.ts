import { point } from '@turf/helpers';
import distance from '@turf/distance';
import booleanIntersects from '@turf/boolean-intersects';
import bboxPolygon from '@turf/bbox-polygon';
import type { IFeature } from '../interactions/interaction.types';
import type { ISpatialQueryEngine } from './spatial-query.interface';
import type { BoundingBox, RadiusQuery, SpatialQueryResult } from './spatial.types';
import { SpatialQueryError, InvalidBoundingBoxError, InvalidGeometryError } from './spatial.errors';

export class SpatialEngine implements ISpatialQueryEngine {
  public findInRadius(features: ReadonlyArray<IFeature>, query: RadiusQuery): SpatialQueryResult {
    const start = performance.now();
    const matchedFeatures: IFeature[] = [];

    if (!Array.isArray(query.center) || query.center.length !== 2) {
      throw new SpatialQueryError('Invalid radius query center point.');
    }

    let originPoint;
    try {
      originPoint = point([query.center[0], query.center[1]]);
    } catch (err) {
      throw new InvalidGeometryError(`Failed to construct origin point: ${err instanceof Error ? err.message : String(err)}`);
    }

    for (const feature of features) {
      if (!this.isValidGeometry(feature.geometry)) {
        continue;
      }

      try {
        // We cast the geometry here since IFeature.geometry is 'unknown' 
        // but we verified it looks like a valid GeoJSON geometry.
        // Turf distance supports Points, Polygons, etc. by calculating distance to the closest part of the geometry.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const dist = distance(originPoint, feature.geometry as any, { units: 'kilometers' });
        
        if (dist <= query.radiusKm) {
          matchedFeatures.push(feature);
        }
      } catch (e) {
        // Silently skip features that Turf fails to process
        console.warn(`SpatialEngine: Failed radius evaluation for feature ${feature.id}`, e);
      }
    }

    const elapsedMs = performance.now() - start;

    return Object.freeze({
      features: Object.freeze(matchedFeatures),
      count: matchedFeatures.length,
      elapsedMs,
    });
  }

  public findInBoundingBox(features: ReadonlyArray<IFeature>, bbox: BoundingBox): SpatialQueryResult {
    const start = performance.now();
    const matchedFeatures: IFeature[] = [];

    if (!Array.isArray(bbox) || bbox.length !== 4) {
      throw new InvalidBoundingBoxError('Bounding box must contain exactly 4 coordinates [minLng, minLat, maxLng, maxLat].');
    }

    // Validate bbox dimensions
    if (bbox[0] > bbox[2] || bbox[1] > bbox[3]) {
      throw new InvalidBoundingBoxError('Invalid bounding box dimensions.');
    }

    let bboxPoly;
    try {
      bboxPoly = bboxPolygon([bbox[0], bbox[1], bbox[2], bbox[3]]);
    } catch (err) {
      throw new InvalidBoundingBoxError(`Failed to construct bounding polygon: ${err instanceof Error ? err.message : String(err)}`);
    }

    for (const feature of features) {
      if (!this.isValidGeometry(feature.geometry)) {
        continue;
      }

      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if (booleanIntersects(bboxPoly, feature.geometry as any)) {
          matchedFeatures.push(feature);
        }
      } catch (e) {
        // Silently skip features that Turf fails to process
        console.warn(`SpatialEngine: Failed bbox intersection for feature ${feature.id}`, e);
      }
    }

    const elapsedMs = performance.now() - start;

    return Object.freeze({
      features: Object.freeze(matchedFeatures),
      count: matchedFeatures.length,
      elapsedMs,
    });
  }

  /**
   * Type guard to ensure the geometry has the minimum viable structure for Turf operations.
   */
  private isValidGeometry(geometry: unknown): boolean {
    if (!geometry || typeof geometry !== 'object') return false;
    const geom = geometry as Record<string, unknown>;
    return typeof geom.type === 'string' && Array.isArray(geom.coordinates);
  }
}
