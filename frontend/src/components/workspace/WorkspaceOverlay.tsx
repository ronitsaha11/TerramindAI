import { PanelManager } from './PanelManager'
import { ToastContainer } from '@/shared/components/ToastContainer'
import { NaturalQueryPanel } from '@/features/spatial/components/NaturalQueryPanel'

export function WorkspaceOverlay() {
  return (
    <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden flex flex-col">
      <NaturalQueryPanel />
      <PanelManager />
      <ToastContainer />
    </div>
  )
}
