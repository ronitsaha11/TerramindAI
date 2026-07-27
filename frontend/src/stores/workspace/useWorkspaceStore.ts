import { create } from 'zustand'

type WorkspaceState = {
  leftSidebarOpen: boolean
  rightSidebarOpen: boolean
  toggleLeftSidebar: () => void
  toggleRightSidebar: () => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  leftSidebarOpen: true,
  rightSidebarOpen: false,
  toggleLeftSidebar: () =>
    set((state) => ({ leftSidebarOpen: !state.leftSidebarOpen })),
  toggleRightSidebar: () =>
    set((state) => ({ rightSidebarOpen: !state.rightSidebarOpen })),
}))
