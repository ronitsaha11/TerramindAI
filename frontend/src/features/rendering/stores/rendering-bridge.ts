import type { RenderingCoordinator } from '../RenderingCoordinator';
import { useRenderingStore } from './use-rendering-store';

/**
 * The RenderingBridge connects the pure domain RenderingCoordinator to the React Zustand store.
 * 
 * Responsibilities:
 * - Subscribes to the RenderingCoordinator's lifecycle events.
 * - Forwards lifecycle state changes to the Zustand projection.
 * - (Does NOT forward 60FPS context updates to Zustand, to avoid React re-renders)
 */
export class RenderingBridge {
  private readonly coordinator: RenderingCoordinator;
  private unsubscribeLifecycle: (() => void) | null = null;

  constructor(coordinator: RenderingCoordinator) {
    this.coordinator = coordinator;
  }

  public initialize(): void {
    // 1. Initial sync
    useRenderingStore.getState().setLifecycleState(this.coordinator.getLifecycleState());

    // 2. Subscribe to domain changes
    this.unsubscribeLifecycle = this.coordinator.events.onLifecycleChanged((state) => {
      useRenderingStore.getState().setLifecycleState(state);
    });
  }

  public destroy(): void {
    if (this.unsubscribeLifecycle) {
      this.unsubscribeLifecycle();
      this.unsubscribeLifecycle = null;
    }
  }
}
