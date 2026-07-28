import type { CameraState } from '../../core/camera/CameraTypes';
import type { Vector3 } from '../../core/planet/PlanetTypes';

/**
 * An approximation of global lighting for rendering.
 */
export interface LightingState {
  /** The normalized directional vector of the Sun in ECEF coordinates */
  sunDirectionEcef: Vector3;
  /** Sun intensity scalar (0.0 to 1.0) */
  sunIntensity: number;
}

/**
 * The strongly typed RenderingContext passed to Renderer Adapters.
 * This object is strictly read-only for consumers.
 */
export interface RenderingContext {
  camera: Readonly<CameraState>;
  lighting: Readonly<LightingState>;
}
