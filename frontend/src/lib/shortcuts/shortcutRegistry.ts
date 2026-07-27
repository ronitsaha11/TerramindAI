import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'

export type ShortcutConfig = {
  id: string
  description: string
  keys: string
  category: string
  enabled: () => boolean
  handler: () => void
}

export const shortcutRegistry: ShortcutConfig[] = [
  {
    id: 'toggle-command-palette',
    description: 'Toggle Command Palette',
    keys: 'mod+k',
    category: 'Workspace',
    enabled: () => true,
    handler: () => {
      const state = useWorkspaceStore.getState()
      state.setCommandPaletteOpen(!state.commandPaletteOpen)
    }
  },
  {
    id: 'toggle-left-sidebar',
    description: 'Toggle Left Sidebar',
    keys: 'mod+b',
    category: 'Workspace',
    enabled: () => true,
    handler: () => useWorkspaceStore.getState().toggleLeftSidebar()
  },
  {
    id: 'toggle-right-sidebar',
    description: 'Toggle Right Sidebar',
    keys: 'mod+\\',
    category: 'Workspace',
    enabled: () => true,
    handler: () => useWorkspaceStore.getState().toggleRightSidebar()
  },
  {
    id: 'hierarchical-escape',
    description: 'Hierarchical Escape Hatch',
    keys: 'escape',
    category: 'Global',
    enabled: () => true,
    handler: () => {
      const state = useWorkspaceStore.getState()
      
      // 1. Command Palette open
      if (state.commandPaletteOpen) {
        state.setCommandPaletteOpen(false)
        return
      }

      // 2. Workspace panels open
      if (state.activePanels.length > 0) {
        state.closeTopmostPanel()
        return
      }

      // 3. Active map tool (stub)
      const hasActiveMapTool = false
      if (hasActiveMapTool) {
        // cancelActiveMapTool()
        return
      }

      // 4. Viewport interaction (stub)
      const hasViewportInteraction = false
      if (hasViewportInteraction) {
        // resetViewportInteraction()
        return
      }
    }
  },
  {
    id: 'delete-placeholder',
    description: 'Reserved placeholder',
    keys: 'delete',
    category: 'System',
    enabled: () => true,
    handler: () => console.log('Delete pressed (placeholder)')
  },
  {
    id: 'f1-placeholder',
    description: 'Reserved placeholder',
    keys: 'f1',
    category: 'System',
    enabled: () => true,
    handler: () => console.log('F1 pressed (placeholder)')
  }
]
