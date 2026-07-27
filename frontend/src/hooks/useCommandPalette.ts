import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'

export function useCommandPalette() {
  const commandPaletteOpen = useWorkspaceStore(state => state.commandPaletteOpen)
  const setCommandPaletteOpen = useWorkspaceStore(state => state.setCommandPaletteOpen)

  return {
    isOpen: commandPaletteOpen,
    setIsOpen: setCommandPaletteOpen,
  }
}

