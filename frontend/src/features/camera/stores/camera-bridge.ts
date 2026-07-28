import type { CameraEngine } from '../../../core/camera/CameraEngine';
import { useCameraDomainStore } from './use-camera-store';

/**
 * The CameraBridge connects the domain CameraEngine to the React Zustand store.
 * 
 * Responsibilities:
 * - Subscribes to the CameraEngine.
 * - Receives immutable state snapshots.
 * - Forwards those snapshots to the Zustand projection.
 * - Throttles UI updates to avoid 60FPS React renders where possible.
 */
export class CameraBridge {
  private readonly engine: CameraEngine;
  private unsubscribeMoved: (() => void) | null = null;
  private unsubscribeReset: (() => void) | null = null;
  private unsubscribeConfig: (() => void) | null = null;

  // Throttle updates to UI (e.g. max 15 times a second for coordinate readouts)
  private lastUpdateMs = 0;
  private readonly UI_UPDATE_THROTTLE_MS = 66; 

  constructor(engine: CameraEngine) {
    this.engine = engine;
  }

  public initialize(): void {
    const store = useCameraDomainStore.getState();

    // 1. Initial sync
    const initialState = this.engine.getState();
    store.setCamera(initialState);
    this.lastUpdateMs = performance.now();

    // 2. Subscribe to domain changes
    this.unsubscribeMoved = this.engine.events.onMoved((state) => {
      const now = performance.now();
      if (now - this.lastUpdateMs >= this.UI_UPDATE_THROTTLE_MS) {
        useCameraDomainStore.getState().setCamera(state);
        this.lastUpdateMs = now;
      }
    });

    const forceSync = () => {
      useCameraDomainStore.getState().setCamera(this.engine.getState());
      this.lastUpdateMs = performance.now();
    };

    this.unsubscribeReset = this.engine.events.onReset(forceSync);
    this.unsubscribeConfig = this.engine.events.onConfigurationChanged(forceSync);
  }

  public destroy(): void {
    if (this.unsubscribeMoved) this.unsubscribeMoved();
    if (this.unsubscribeReset) this.unsubscribeReset();
    if (this.unsubscribeConfig) this.unsubscribeConfig();

    this.unsubscribeMoved = null;
    this.unsubscribeReset = null;
    this.unsubscribeConfig = null;
  }
}
