import type { CameraEngine } from '../../core/camera/CameraEngine';
import type { EarthEphemeris } from '../../core/planet/EarthEphemeris';
import type { RendererAdapter } from './RendererAdapter';
import type { RenderingContext } from './RenderingTypes';
import { RenderingLifecycleState } from './RenderingLifecycle';
import { RenderingEvents } from './RenderingEvents';
import { RenderingValidation } from './RenderingValidation';
import { SunLightingMath } from './utils/SunLightingMath';

/**
 * The strict boundary coordinator between pure domain state and the rendering implementation.
 */
export class RenderingCoordinator {
  public readonly events = new RenderingEvents();
  
  private _lifecycleState: RenderingLifecycleState = RenderingLifecycleState.UNINITIALIZED;
  private _adapter: RendererAdapter | null = null;
  
  // The zero-allocation context payload
  private readonly _context: RenderingContext;

  private unsubCamera: (() => void) | null = null;
  private unsubEphemeris: (() => void) | null = null;

  private readonly cameraEngine: CameraEngine;
  private readonly earthEphemeris: EarthEphemeris;

  constructor(
    cameraEngine: CameraEngine,
    earthEphemeris: EarthEphemeris
  ) {
    this.cameraEngine = cameraEngine;
    this.earthEphemeris = earthEphemeris;

    // Allocate the unified payload strictly once
    this._context = {
      camera: this.cameraEngine.getState(),
      lighting: {
        sunDirectionEcef: { x: 1, y: 0, z: 0 },
        sunIntensity: 1.0
      }
    };
  }

  /**
   * Attaches a specific renderer implementation to the coordinator.
   */
  public attachAdapter(adapter: RendererAdapter): void {
    RenderingValidation.assertState(this._lifecycleState, RenderingLifecycleState.UNINITIALIZED, 'attachAdapter');
    this._adapter = adapter;
  }

  /**
   * Initializes the attached renderer and begins observing the domain.
   */
  public async start(): Promise<void> {
    RenderingValidation.assertState(this._lifecycleState, RenderingLifecycleState.UNINITIALIZED, 'start');
    RenderingValidation.assertAdapterAttached(this._adapter);

    this.setLifecycleState(RenderingLifecycleState.MOUNTING);

    try {
      const initialized = await this._adapter!.initialize();
      if (!initialized) {
        this.setLifecycleState(RenderingLifecycleState.ERROR);
        return;
      }

      this.setLifecycleState(RenderingLifecycleState.READY);

      // Perform an initial manual sync to prime the renderer
      this.syncContext();

      // Subscribe to domain events
      this.unsubCamera = this.cameraEngine.events.onMoved(() => this.syncContext());
      
      this.unsubEphemeris = this.earthEphemeris.events.onUpdated(() => {
        // We only explicitly trigger a context sync on ephemeris updates if lighting changed.
        // During rapid simulation ticks, syncContext gets called anyway.
        this.syncContext();
      });

    } catch (e) {
      console.error('[RenderingCoordinator] Failed to start:', e);
      this.setLifecycleState(RenderingLifecycleState.ERROR);
    }
  }

  /**
   * Cleans up the coordinator and destroys the attached adapter.
   */
  public destroy(): void {
    if (this._lifecycleState === RenderingLifecycleState.DESTROYED) return;

    if (this.unsubCamera) this.unsubCamera();
    if (this.unsubEphemeris) this.unsubEphemeris();

    this.unsubCamera = null;
    this.unsubEphemeris = null;

    if (this._adapter) {
      this._adapter.destroy();
      this._adapter = null;
    }

    this.setLifecycleState(RenderingLifecycleState.DESTROYED);
  }

  public getLifecycleState(): RenderingLifecycleState {
    return this._lifecycleState;
  }

  private setLifecycleState(state: RenderingLifecycleState): void {
    this._lifecycleState = state;
    this.events.dispatchLifecycle(state);
  }

  /**
   * Pulls the latest domain states, updates the shared zero-allocation context,
   * and pushes it down to the renderer adapter.
   */
  private syncContext(): void {
    if (this._lifecycleState !== RenderingLifecycleState.READY || !this._adapter) return;

    // The context's camera property is already referencing the engine's state object or we can explicitly assign
    this._context.camera = this.cameraEngine.getState();

    // Update lighting inline
    SunLightingMath.calculateSunDirectionEcef(
      this.earthEphemeris.getState(),
      this._context.lighting.sunDirectionEcef
    );

    // Provide the read-only unified context to the adapter
    this._adapter.applyContext(this._context);
    
    // Notify local subscribers that a sync occurred
    this.events.dispatchContextUpdate();
  }
}
