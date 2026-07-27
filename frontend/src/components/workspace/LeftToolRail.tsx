import { 
  Layers, 
  CloudRain, 
  Cpu, 
  LineChart, 
  Server, 
  Settings 
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function LeftToolRail() {
  const tools = [
    { icon: Layers, label: 'Layers' },
    { icon: CloudRain, label: 'Weather' },
    { icon: Cpu, label: 'AI' },
    { icon: LineChart, label: 'Analytics' },
    { icon: Server, label: 'Jobs' },
    { icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="w-12 bg-zinc-950 border-r border-zinc-800 flex flex-col items-center py-4 gap-4 shrink-0">
      {tools.map((tool) => (
        <Tooltip key={tool.label}>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" aria-label={tool.label} className="text-zinc-400 hover:text-zinc-50">
              <tool.icon className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>{tool.label}</p>
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}
