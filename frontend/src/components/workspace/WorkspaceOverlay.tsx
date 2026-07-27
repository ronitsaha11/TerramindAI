import { PanelManager } from './PanelManager'

export function WorkspaceOverlay() {
  return (
    <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
      <PanelManager />
    </div>
  )
}
