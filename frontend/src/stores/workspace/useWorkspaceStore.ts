import { create } from 'zustand'

type WorkspaceState = {
  leftSidebarOpen: boolean
  rightSidebarOpen: boolean
  toggleLeftSidebar: () => void
  toggleRightSidebar: () => void

  activePanels: string[]
  openPanel: (id: string) => void
  closePanel: (id: string) => void
  togglePanel: (id: string) => void

  commandPaletteOpen: boolean
  setCommandPaletteOpen: (open: boolean) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  leftSidebarOpen: true,
  rightSidebarOpen: false,
  toggleLeftSidebar: () =>
    set((state) => ({ leftSidebarOpen: !state.leftSidebarOpen })),
  toggleRightSidebar: () =>
    set((state) => ({ rightSidebarOpen: !state.rightSidebarOpen })),

  activePanels: [],
  openPanel: (id) =>
    set((state) => ({
      activePanels: state.activePanels.includes(id)
        ? state.activePanels
        : [...state.activePanels, id],
    })),
  closePanel: (id) =>
    set((state) => ({
      activePanels: state.activePanels.filter((panelId) => panelId !== id),
    })),
  togglePanel: (id) => {
    const isActive = get().activePanels.includes(id)
    if (isActive) {
      get().closePanel(id)
    } else {
      get().openPanel(id)
    }
  },

  commandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}))

export const isPanelOpen = (state: WorkspaceState, id: string) =>
  state.activePanels.includes(id)
