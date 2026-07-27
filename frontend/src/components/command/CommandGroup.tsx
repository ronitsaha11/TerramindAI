import { CommandGroup as UICommandGroup } from '@/components/ui/command'
import { type ReactNode } from 'react'

type Props = {
  heading: string
  children: ReactNode
}

export function CommandGroup({ heading, children }: Props) {
  return (
    <UICommandGroup 
      heading={heading} 
      className="text-zinc-400 [&_[cmdk-group-heading]]:px-4 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:uppercase"
    >
      {children}
    </UICommandGroup>
  )
}
