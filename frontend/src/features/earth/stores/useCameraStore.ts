import { create } from 'zustand'
import { type CameraPosition } from '../types/camera.types'

const DEFAULT_CAMERA: CameraPosition = {
  longitude: 0,
  latitude: 20,
  zoom: 2,
  pitch: 0,
  bearing: 0,
}

type CameraStoreState = {
  camera: CameraPosition
  isMoving: boolean
  setCamera: (camera: CameraPosition) => void
  setMoving: (moving: boolean) => void
  reset: () => void
}

export const useCameraStore = create<CameraStoreState>((set) => ({
  camera: DEFAULT_CAMERA,
  isMoving: false,
  setCamera: (camera) => set({ camera }),
  setMoving: (moving) => set({ isMoving: moving }),
  reset: () => set({ camera: DEFAULT_CAMERA, isMoving: false }),
}))
