import { create } from 'zustand'

export type WorkspaceStatusState = {
  workspaceStatus: string
  projection: string
  zoom: number
  latitude: number
  longitude: number
  fps: number | null
  networkStatus: string
  jobCount: number
  notificationCount: number

  setWorkspaceStatus: (val: string) => void
  setProjection: (val: string) => void
  setZoom: (val: number) => void
  setLatitude: (val: number) => void
  setLongitude: (val: number) => void
  setFPS: (val: number | null) => void
  setNetworkStatus: (val: string) => void
  setJobCount: (val: number) => void
  setNotificationCount: (val: number) => void
}

export const useWorkspaceStatusStore = create<WorkspaceStatusState>((set) => ({
  workspaceStatus: 'SYSTEM NORMAL',
  projection: 'EPSG:4326',
  zoom: 4.00,
  latitude: 0.0000,
  longitude: 0.0000,
  fps: null,
  networkStatus: 'ONLINE',
  jobCount: 0,
  notificationCount: 0,

  setWorkspaceStatus: (val) => set({ workspaceStatus: val }),
  setProjection: (val) => set({ projection: val }),
  setZoom: (val) => set({ zoom: val }),
  setLatitude: (val) => set({ latitude: val }),
  setLongitude: (val) => set({ longitude: val }),
  setFPS: (val) => set({ fps: val }),
  setNetworkStatus: (val) => set({ networkStatus: val }),
  setJobCount: (val) => set({ jobCount: val }),
  setNotificationCount: (val) => set({ notificationCount: val }),
}))
