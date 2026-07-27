import { Button } from '@/components/ui/button'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { PanelLeft, PanelRight, Globe } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useCommandPalette } from '@/hooks/useCommandPalette'

export function TopNav() {
  const toggleLeftSidebar = useWorkspaceStore((state) => state.toggleLeftSidebar)
  const toggleRightSidebar = useWorkspaceStore((state) => state.toggleRightSidebar)
  const { setIsOpen } = useCommandPalette()

  return (
    <header className="h-12 bg-zinc-950 border-b border-zinc-800 px-4 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3 font-semibold tracking-tight">
        <Globe className="h-5 w-5 text-zinc-400" />
        TerraMind Earth Intelligence
        
        {/* Subtle command palette shortcut hint */}
        <button 
          onClick={() => setIsOpen(true)}
          className="ml-4 flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/50 px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-400 hover:bg-zinc-800 transition-colors"
          aria-label="Open Command Palette"
        >
          <span className="hidden sm:inline">Search commands...</span>
          <kbd className="pointer-events-none hidden sm:inline-flex h-4 select-none items-center gap-1 rounded border border-zinc-700 bg-zinc-800 px-1.5 font-mono text-[10px] font-medium text-zinc-400">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
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
