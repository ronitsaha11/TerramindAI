import { create } from 'zustand';
import type { CameraStoreState } from './camera-store.types';
import { DEFAULT_CAMERA_CONFIG } from '../../../core/camera/CameraConfig';

/**
 * Zustand projection of the pure domain CameraEngine state.
 * 
 * Do NOT attempt to mutate state here.
 * All mutations MUST go through the domain CameraEngine.
 */
export const useCameraDomainStore = create<CameraStoreState>((set) => ({
  camera: { ...DEFAULT_CAMERA_CONFIG.initialState },

  setCamera: (camera) => {
    set({ camera: { ...camera } });
  },

  reset: (camera) => {
    set({ camera: { ...camera } });
  },
}));
