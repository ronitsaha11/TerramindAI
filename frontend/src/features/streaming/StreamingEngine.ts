import type { CameraEngine } from '../../core/camera/CameraEngine';
import type { CameraState } from '../../core/camera/CameraTypes';
import { StreamingPolicy } from './StreamingPolicy';
import { StreamingCache } from './StreamingCache';
import { StreamingEvents } from './StreamingEvents';
import { DEFAULT_CACHE_POLICY } from './StreamingConfig';
import type { CachePolicy, StreamingPolicyState } from './StreamingTypes';

export class StreamingEngine {
  public readonly events = new StreamingEvents();
  
  private policy: StreamingPolicy;
  private cache: StreamingCache;
  private cameraEngine: CameraEngine;
  private unsubCamera: (() => void) | null = null;

  constructor(cameraEngine: CameraEngine, cachePolicy: CachePolicy = DEFAULT_CACHE_POLICY) {
    this.cameraEngine = cameraEngine;
    this.policy = new StreamingPolicy();
    this.cache = new StreamingCache(cachePolicy);
  }

  public initialize(): void {
    // Subscribe to camera updates to drive the streaming policy
    this.unsubCamera = this.cameraEngine.events.onMoved((state: Readonly<CameraState>) => {
      this.policy.calculateLOD(state);
    });

    // Run initial LOD calculation
    this.policy.calculateLOD(this.cameraEngine.getState());
  }

  public destroy(): void {
    if (this.unsubCamera) {
      this.unsubCamera();
      this.unsubCamera = null;
    }
  }

  public getPolicyState(): Readonly<StreamingPolicyState> {
    return this.policy.getState();
  }

  public getCache(): StreamingCache {
    return this.cache;
  }
}
