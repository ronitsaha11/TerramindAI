import { create } from 'zustand';
import type { RenderingStoreState } from './rendering-store.types';
import { RenderingLifecycleState } from '../RenderingLifecycle';

/**
 * Zustand projection of the Rendering Foundation's lifecycle state.
 * Allows React components (e.g., loading screens) to react to renderer startup.
 */
export const useRenderingStore = create<RenderingStoreState>((set) => ({
  lifecycleState: RenderingLifecycleState.UNINITIALIZED,

  setLifecycleState: (state) => {
    set({ lifecycleState: state });
  },
}));
