import { RenderingLifecycleState } from './RenderingLifecycle';

export type LifecycleListener = (state: RenderingLifecycleState) => void;
export type ContextUpdateListener = () => void;

/**
 * Local event emitter for rendering foundation state changes.
 */
export class RenderingEvents {
  private lifecycleListeners: LifecycleListener[] = [];
  private updateListeners: ContextUpdateListener[] = [];

  public onLifecycleChanged(listener: LifecycleListener): () => void {
    this.lifecycleListeners.push(listener);
    return () => this.removeListener(this.lifecycleListeners, listener);
  }

  public onContextUpdated(listener: ContextUpdateListener): () => void {
    this.updateListeners.push(listener);
    return () => this.removeListener(this.updateListeners, listener);
  }

  public dispatchLifecycle(state: RenderingLifecycleState): void {
    for (let i = 0; i < this.lifecycleListeners.length; i++) {
      this.lifecycleListeners[i](state);
    }
  }

  public dispatchContextUpdate(): void {
    for (let i = 0; i < this.updateListeners.length; i++) {
      this.updateListeners[i]();
    }
  }

  private removeListener<T>(arr: T[], listener: T): void {
    const idx = arr.indexOf(listener);
    if (idx !== -1) {
      arr.splice(idx, 1);
    }
  }
}
