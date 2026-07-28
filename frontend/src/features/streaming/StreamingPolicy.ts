import type { CameraState } from '../../core/camera/CameraTypes';
import { DEFAULT_STREAMING_POLICY } from './StreamingConfig';
import type { StreamingPolicyState } from './StreamingTypes';

export class StreamingPolicy {
  private state: StreamingPolicyState;

  constructor() {
    this.state = {
      minZoom: DEFAULT_STREAMING_POLICY.minZoom,
      maxZoom: DEFAULT_STREAMING_POLICY.maxZoom,
      currentLOD: 0,
      retainParents: DEFAULT_STREAMING_POLICY.retainParents
    };
  }

  /**
   * Calculates the target Level Of Detail (LOD) based on the camera's altitude.
   * Uses a logarithmic scale similar to standard slippy map zoom levels.
   */
  public calculateLOD(camera: Readonly<CameraState>): number {
    const { altitude } = camera;
    
    // Safety fallback for extreme close-ups or space
    if (altitude <= 0) return this.state.maxZoom;
    if (altitude > 35000000) return this.state.minZoom;

    // Approximate zoom = log2(base_altitude / altitude)
    // where base_altitude is roughly Earth's circumference / tile width
    const zoom = Math.log2(35000000 / altitude);
    
    // Clamp to configured limits
    const clampedZoom = Math.max(
      this.state.minZoom, 
      Math.min(this.state.maxZoom, Math.round(zoom))
    );

    this.state.currentLOD = clampedZoom;
    return clampedZoom;
  }

  public getState(): Readonly<StreamingPolicyState> {
    return this.state;
  }
}
