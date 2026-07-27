import { Button } from '@/components/ui/button'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { PanelLeft, PanelRight, Globe } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function TopNav() {
  const toggleLeftSidebar = useWorkspaceStore((state) => state.toggleLeftSidebar)
  const toggleRightSidebar = useWorkspaceStore((state) => state.toggleRightSidebar)

  return (
    <header className="h-12 bg-zinc-950 border-b border-zinc-800 px-4 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-2 font-semibold tracking-tight">
        <Globe className="h-5 w-5 text-zinc-400" />
        TerraMind Earth Intelligence
      </div>
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={toggleLeftSidebar} aria-label="Toggle Left Sidebar" className="text-zinc-400 hover:text-zinc-50">
              <PanelLeft className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>Toggle Left Sidebar</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={toggleRightSidebar} aria-label="Toggle Right Sidebar" className="text-zinc-400 hover:text-zinc-50">
              <PanelRight className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>Toggle Right Sidebar</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </header>
  )
}
