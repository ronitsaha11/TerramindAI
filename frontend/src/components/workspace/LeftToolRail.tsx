import { 
  Folder,
  Layers, 
  Database,
  CloudRain, 
  Cpu, 
  LineChart, 
  Server, 
  Settings 
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { cn } from '@/lib/utils'

export function LeftToolRail() {
  const togglePanel = useWorkspaceStore(state => state.togglePanel)
  const activePanels = useWorkspaceStore(state => state.activePanels)

  const tools = [
    { id: 'projects', icon: Folder, label: 'Projects' },
    { id: 'layers', icon: Layers, label: 'Layers' },
    { id: 'datasets', icon: Database, label: 'Datasets' },
    { id: 'weather', icon: CloudRain, label: 'Weather' },
    { id: 'ai', icon: Cpu, label: 'AI' },
    { id: 'analytics', icon: LineChart, label: 'Analytics' },
    { id: 'jobs', icon: Server, label: 'Jobs' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="w-12 bg-zinc-950 border-r border-zinc-800 flex flex-col items-center py-4 gap-4 shrink-0">
      {tools.map((tool) => {
        const isActive = activePanels.includes(tool.id)
        return (
          <Tooltip key={tool.id}>
            <TooltipTrigger asChild>
              <Button 
                variant="ghost" 
                size="icon" 
                aria-label={tool.label} 
                className={cn(
                  "hover:text-zinc-50",
                  isActive ? "text-zinc-50 bg-zinc-800" : "text-zinc-400"
                )}
                onClick={() => togglePanel(tool.id)}
              >
                <tool.icon className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>{tool.label}</p>
            </TooltipContent>
          </Tooltip>
        )
      })}
    </div>
  )
}
