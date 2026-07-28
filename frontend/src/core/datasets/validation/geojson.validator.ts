import type { IDatasetValidator } from '../contracts/validator.interface';
import type { IValidationResult, IValidationIssue } from './validation.types';

/**
 * Validates GeoJSON structures.
 * Responsibility: Performs structural validation on input data to ensure it adheres to basic GeoJSON rules.
 * Ownership: Operates purely on input data without mutating it, generating metadata, or creating datasets.
 */
export class GeoJsonValidator implements IDatasetValidator<unknown> {
  public async validate(input: unknown): Promise<IValidationResult> {
    const issues: IValidationIssue[] = [];

    if (!input || typeof input !== 'object') {
      issues.push({
        code: 'GEOJSON_INVALID_TYPE',
        message: 'Input must be an object.',
        severity: 'error',
      });
      return { isValid: false, issues };
    }

    const geojson = input as Record<string, unknown>;

    if (!('type' in geojson) || typeof geojson.type !== 'string') {
      issues.push({
        code: 'GEOJSON_MISSING_TYPE',
        message: 'Input must have a "type" string property.',
        severity: 'error',
      });
      return { isValid: false, issues };
    }

    if (geojson.type === 'FeatureCollection') {
      if (!Array.isArray(geojson.features)) {
        issues.push({
          code: 'GEOJSON_INVALID_FEATURES',
          message: 'FeatureCollection must have a "features" array.',
          severity: 'error',
          path: 'features',
        });
      } else {
        // Lightweight validation of first few features to avoid heavy processing
        const maxFeaturesToValidate = Math.min(geojson.features.length, 10);
        for (let i = 0; i < maxFeaturesToValidate; i++) {
          const feature = geojson.features[i];
          if (!feature || typeof feature !== 'object') {
            issues.push({
              code: 'GEOJSON_INVALID_FEATURE',
              message: `Feature at index ${i} is not a valid object.`,
              severity: 'error',
              path: `features[${i}]`,
            });
            continue;
          }
          const f = feature as Record<string, unknown>;
          if (f.type !== 'Feature') {
            issues.push({
              code: 'GEOJSON_INVALID_FEATURE_TYPE',
              message: `Feature at index ${i} must have type "Feature".`,
              severity: 'error',
              path: `features[${i}].type`,
            });
          }
          if (!('geometry' in f)) {
            issues.push({
              code: 'GEOJSON_MISSING_GEOMETRY',
              message: `Feature at index ${i} is missing "geometry".`,
              severity: 'error',
              path: `features[${i}].geometry`,
            });
          }
          if (!('properties' in f)) {
            issues.push({
              code: 'GEOJSON_MISSING_PROPERTIES',
              message: `Feature at index ${i} is missing "properties".`,
              severity: 'error',
              path: `features[${i}].properties`,
            });
          }
        }
      }
    } else if (geojson.type === 'Feature') {
      if (!('geometry' in geojson)) {
        issues.push({
          code: 'GEOJSON_MISSING_GEOMETRY',
          message: 'Feature is missing "geometry".',
          severity: 'error',
          path: 'geometry',
        });
      }
      if (!('properties' in geojson)) {
        issues.push({
          code: 'GEOJSON_MISSING_PROPERTIES',
          message: 'Feature is missing "properties".',
          severity: 'error',
          path: 'properties',
        });
      }
    } else {
      // For this sprint, we only strictly validate FeatureCollection and Feature,
      // but others (Geometry types) are permitted if they have a 'type'.
      issues.push({
        code: 'GEOJSON_UNSUPPORTED_TYPE_WARNING',
        message: `GeoJSON type "${geojson.type}" is supported but not strictly validated.`,
        severity: 'warning',
        path: 'type',
      });
    }

    const hasError = issues.some(issue => issue.severity === 'error');

    return {
      isValid: !hasError,
      issues,
    };
  }
}
