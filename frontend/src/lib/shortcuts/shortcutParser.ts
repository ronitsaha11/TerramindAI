export const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.userAgent)

export function matchShortcut(event: KeyboardEvent, shortcut: string): boolean {
  const parts = shortcut.toLowerCase().split('+')
  
  let needsMod = false
  let needsCtrl = false
  let needsShift = false
  let needsAlt = false
  let key = ''

  for (const part of parts) {
    if (part === 'mod') needsMod = true
    else if (part === 'ctrl') needsCtrl = true
    else if (part === 'shift') needsShift = true
    else if (part === 'alt') needsAlt = true
    else key = part
  }

  const hasMod = isMac ? event.metaKey : event.ctrlKey
  const hasCtrl = event.ctrlKey
  const hasShift = event.shiftKey
  const hasAlt = event.altKey

  if (needsMod && !hasMod) return false
  if (needsCtrl && !hasCtrl) return false
  if (needsShift && !hasShift) return false
  if (needsAlt && !hasAlt) return false

  // Don't trigger if unexpected modifiers are pressed
  if (!needsMod && !needsCtrl && hasMod && !isMac) return false
  if (!needsMod && hasMod && isMac) return false
  if (!needsShift && hasShift) return false
  if (!needsAlt && hasAlt) return false

  // Compare key string natively
  return event.key.toLowerCase() === key
}

export function formatShortcut(shortcut: string): string {
  if (isMac) {
    return shortcut.replace(/mod/i, '⌘').toUpperCase().replace(/\+/g, '')
  }
  return shortcut.replace(/mod/i, 'Ctrl').toUpperCase()
}
