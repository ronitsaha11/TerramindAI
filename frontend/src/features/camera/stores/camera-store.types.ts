import type { CameraState } from '../../../core/camera/CameraTypes';

export interface CameraStoreState {
  camera: CameraState;
  
  setCamera: (camera: Readonly<CameraState>) => void;
  reset: (camera: Readonly<CameraState>) => void;
}
