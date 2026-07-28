import { RenderingLifecycleState } from './RenderingLifecycle';

export class RenderingValidation {
  /**
   * Asserts that a method is called only when the coordinator is in a specific state.
   */
  public static assertState(currentState: RenderingLifecycleState, expectedState: RenderingLifecycleState, context: string): void {
    if (currentState !== expectedState) {
      throw new Error(`[RenderingValidation] Invalid lifecycle state in ${context}. Expected ${expectedState}, got ${currentState}.`);
    }
  }

  /**
   * Asserts that an adapter is attached before coordinating render updates.
   */
  public static assertAdapterAttached(adapter: unknown | null): void {
    if (!adapter) {
      throw new Error('[RenderingValidation] No RendererAdapter attached to the coordinator.');
    }
  }
}
