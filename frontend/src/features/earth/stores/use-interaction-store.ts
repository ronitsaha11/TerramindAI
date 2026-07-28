import { create } from 'zustand';
import type { InteractionStoreState } from './interaction-store.types';
import type { InteractionState } from '../../../core/interactions/interaction.types';

/**
 * Zustand projection of the immutable interaction domain state.
 * 
 * Do NOT attempt to mutate state here (e.g., setHovered). 
 * All mutations MUST go through the domain InteractionManager.
 */
export const useInteractionStore = create<InteractionStoreState>((set) => ({
  hoveredFeature: null,
  selectedFeature: null,
  cursorX: null,
  cursorY: null,
  initialized: false,

  setSnapshot: (snapshot: Readonly<InteractionState>) => {
    set({
      hoveredFeature: snapshot.hoveredFeature,
      selectedFeature: snapshot.selectedFeature,
      cursorX: snapshot.cursorX,
      cursorY: snapshot.cursorY,
    });
  },

  setInitialized: (initialized: boolean) => {
    set({ initialized });
  },
}));
