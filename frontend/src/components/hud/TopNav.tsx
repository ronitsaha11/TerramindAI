import { Button } from '@/components/ui/button'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'

export function TopNav() {
  const toggleLeftSidebar = useWorkspaceStore((state) => state.toggleLeftSidebar)
  const toggleRightSidebar = useWorkspaceStore((state) => state.toggleRightSidebar)

  return (
    <header className="h-12 bg-zinc-950 border-b border-zinc-800 px-4 flex items-center justify-between shrink-0">
      <div className="font-semibold tracking-tight">
        TerraMind Earth Intelligence
      </div>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={toggleLeftSidebar} aria-label="Toggle Left Sidebar">
          Toggle Left Sidebar
        </Button>
        <Button variant="secondary" size="sm" onClick={toggleRightSidebar} aria-label="Toggle Right Sidebar">
          Toggle Right Sidebar
        </Button>
      </div>
    </header>
  )
}
