import { useEffect } from 'react'
import { shortcutRegistry } from '@/lib/shortcuts/shortcutRegistry'
import { matchShortcut } from '@/lib/shortcuts/shortcutParser'

export function useGlobalShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore input fields unless it's Escape
      const target = e.target as HTMLElement
      if (target) {
        const tagName = target.tagName.toLowerCase()
        if (
          tagName === 'input' || 
          tagName === 'textarea' || 
          tagName === 'select' || 
          target.isContentEditable
        ) {
          if (e.key.toLowerCase() !== 'escape') {
            return
          }
        }
      }

      for (const shortcut of shortcutRegistry) {
        if (matchShortcut(e, shortcut.keys)) {
          if (shortcut.enabled()) {
            e.preventDefault()
            shortcut.handler()
          }
          return // Stop at the first match
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])
}
