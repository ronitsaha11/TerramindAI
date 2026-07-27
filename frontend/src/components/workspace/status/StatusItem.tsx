import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { type ComponentType } from 'react'

type StatusItemProps = {
  label: string
  value: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: ComponentType<any>
}

export function StatusItem({ label, value, icon: Icon }: StatusItemProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button 
          className="flex items-center gap-1.5 px-2 py-1 hover:bg-zinc-800/50 rounded transition-colors text-[10px] uppercase tracking-wider text-zinc-400 font-medium whitespace-nowrap"
          aria-label={label}
        >
          <Icon className="h-3.5 w-3.5 text-zinc-500" />
          <span className="tabular-nums">{value}</span>
        </button>
      </TooltipTrigger>
      <TooltipContent side="top">
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  )
}
