import { type RegistryCommand } from '@/lib/commandRegistry'
import { CommandItem as UICommandItem } from '@/components/ui/command'

type Props = {
  command: RegistryCommand
  onSelect: (command: RegistryCommand) => void
}

export function CommandItem({ command, onSelect }: Props) {
  const Icon = command.icon
  return (
    <UICommandItem
      value={`${command.title} ${command.description} ${command.keywords.join(' ')}`}
      onSelect={() => onSelect(command)}
      className="flex items-center gap-3 px-4 py-3 cursor-pointer aria-selected:bg-zinc-800"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-900 border border-zinc-800">
        <Icon className="h-4 w-4 text-zinc-400" />
      </div>
      <div className="flex flex-col flex-1 gap-1">
        <div className="flex items-center justify-between">
          <span className="font-medium text-sm text-zinc-200">{command.title}</span>
          {command.shortcut && (
            <kbd className="hidden md:inline-flex h-5 items-center gap-1 rounded border border-zinc-700 bg-zinc-800 px-1.5 font-mono text-[10px] font-medium text-zinc-400 opacity-100">
              {command.shortcut}
            </kbd>
          )}
        </div>
        <span className="text-xs text-zinc-500">{command.description}</span>
      </div>
    </UICommandItem>
  )
}
