import type { ViewportQueryController } from '../../earth/services/viewport-query-controller';
import { useSpatialStore } from './useSpatialStore';

export class SpatialBridge {
  private readonly controller: ViewportQueryController;
  private unsubscribe: (() => void) | null = null;

  constructor(controller: ViewportQueryController) {
    this.controller = controller;
  }

  public initialize(): void {
    if (this.unsubscribe) return;
    
    this.unsubscribe = this.controller.subscribe((result) => {
      useSpatialStore.getState().setVisibleResult(result);
    });
  }

  public destroy(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }
}
