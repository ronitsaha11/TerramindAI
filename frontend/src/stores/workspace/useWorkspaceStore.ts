import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

type WorkspaceState = {
  leftSidebarOpen: boolean
  rightSidebarOpen: boolean
  toggleLeftSidebar: () => void
  toggleRightSidebar: () => void

  activePanels: string[]
  openPanel: (id: string) => void
  closePanel: (id: string) => void
  togglePanel: (id: string) => void
  closeTopmostPanel: () => void

  commandPaletteOpen: boolean
  setCommandPaletteOpen: (open: boolean) => void
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
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
      closeTopmostPanel: () =>
        set((state) => ({
          activePanels: state.activePanels.slice(0, -1)
        })),

      commandPaletteOpen: false,
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
    }),
    {
      name: 'terramind-workspace-layout',
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        leftSidebarOpen: state.leftSidebarOpen,
        rightSidebarOpen: state.rightSidebarOpen,
        activePanels: state.activePanels,
      }),
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      migrate: (persistedState: unknown, _version: number) => {
        // Placeholder for future schema migrations
        return persistedState as WorkspaceState
      },
    }
  )
)

export const isPanelOpen = (state: WorkspaceState, id: string) =>
  state.activePanels.includes(id)
