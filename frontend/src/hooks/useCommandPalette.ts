import { useEffect } from 'react'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'

export function useCommandPalette() {
  const commandPaletteOpen = useWorkspaceStore(state => state.commandPaletteOpen)
  const setCommandPaletteOpen = useWorkspaceStore(state => state.setCommandPaletteOpen)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setCommandPaletteOpen(!commandPaletteOpen)
      }
      
      if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [commandPaletteOpen, setCommandPaletteOpen])

  return {
    isOpen: commandPaletteOpen,
    setIsOpen: setCommandPaletteOpen,
  }
}
