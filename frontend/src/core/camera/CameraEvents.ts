import type { CameraState } from './CameraTypes';

export type CameraMovedListener = (state: Readonly<CameraState>) => void;
export type CameraStateListener = () => void;

/**
 * Lightweight domain-local event emitter for the Camera Framework.
 */
export class CameraEvents {
  private movedListeners: CameraMovedListener[] = [];
  private resetListeners: CameraStateListener[] = [];
  private configChangedListeners: CameraStateListener[] = [];

  public onMoved(listener: CameraMovedListener): () => void {
    this.movedListeners.push(listener);
    return () => this.removeListener(this.movedListeners, listener);
  }

  public onReset(listener: CameraStateListener): () => void {
    this.resetListeners.push(listener);
    return () => this.removeListener(this.resetListeners, listener);
  }

  public onConfigurationChanged(listener: CameraStateListener): () => void {
    this.configChangedListeners.push(listener);
    return () => this.removeListener(this.configChangedListeners, listener);
  }

  public dispatchMoved(state: Readonly<CameraState>): void {
    for (let i = 0; i < this.movedListeners.length; i++) {
      this.movedListeners[i](state);
    }
  }

  public dispatchReset(): void {
    for (let i = 0; i < this.resetListeners.length; i++) {
      this.resetListeners[i]();
    }
  }

  public dispatchConfigurationChanged(): void {
    for (let i = 0; i < this.configChangedListeners.length; i++) {
      this.configChangedListeners[i]();
    }
  }

  private removeListener<T>(arr: T[], listener: T): void {
    const idx = arr.indexOf(listener);
    if (idx !== -1) {
      arr.splice(idx, 1);
    }
  }
}
