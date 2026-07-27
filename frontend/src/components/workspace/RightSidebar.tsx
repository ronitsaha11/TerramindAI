import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { cn } from '@/lib/utils'
import { Sliders, MousePointer2, Layers, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function RightSidebar() {
  const rightSidebarOpen = useWorkspaceStore((state) => state.rightSidebarOpen)

  const tools = [
    { icon: Sliders, label: 'Properties' },
    { icon: MousePointer2, label: 'Selection' },
    { icon: Layers, label: 'Layers' },
    { icon: Info, label: 'Info' },
  ]

  return (
    <aside
      className={cn(
        "bg-zinc-900 border-l border-zinc-800 overflow-hidden transition-all duration-300 ease-in-out shrink-0 flex",
        rightSidebarOpen ? "w-64" : "w-12"
      )}
    >
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="p-4 w-[13rem] min-w-[13rem]">
          <h2 className="font-semibold text-sm text-zinc-400 uppercase tracking-wider">Inspector</h2>
        </div>
      </div>
      
      {/* Right Icon Rail */}
      <div className="w-12 bg-zinc-950 border-l border-zinc-800 flex flex-col items-center py-4 gap-4 shrink-0">
        {tools.map((tool) => (
          <Tooltip key={tool.label}>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" aria-label={tool.label} className="text-zinc-400 hover:text-zinc-50">
                <tool.icon className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>{tool.label}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </aside>
  )
}
