import type { RenderingContext } from './RenderingTypes';

/**
 * Interface that specific rendering implementations (e.g. MapLibre, Deck.gl) must implement.
 * The RenderingFoundation owns this contract.
 */
export interface RendererAdapter {
  /**
   * Initializes the underlying rendering engine (e.g. instantiating canvases, webgl contexts).
   * @returns true if initialization succeeded.
   */
  initialize(): Promise<boolean>;

  /**
   * Synchronizes the pure domain context (camera, lighting) into the specific renderer.
   * Called automatically by the RenderingCoordinator.
   */
  applyContext(context: Readonly<RenderingContext>): void;

  /**
   * Cleans up resources held by the renderer.
   */
  destroy(): void;
}
