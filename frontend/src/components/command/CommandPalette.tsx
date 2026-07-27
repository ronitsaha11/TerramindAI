import { useCallback, useMemo } from 'react'
import { useCommandPalette } from '@/hooks/useCommandPalette'
import { commandRegistry, type RegistryCommand } from '@/lib/commandRegistry'
import { CommandItem } from './CommandItem'
import { CommandGroup } from './CommandGroup'
import {
  CommandDialog,
  CommandEmpty,
  CommandInput,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'

export function CommandPalette() {
  const { isOpen, setIsOpen } = useCommandPalette()

  const handleSelect = useCallback((command: RegistryCommand) => {
    command.action()
    setIsOpen(false)
  }, [setIsOpen])

  const groupedCommands = useMemo(() => {
    return commandRegistry.reduce((acc, cmd) => {
      const group = cmd.group || 'Other'
      if (!acc[group]) acc[group] = []
      acc[group].push(cmd)
      return acc
    }, {} as Record<string, RegistryCommand[]>)
  }, [])

  return (
    <CommandDialog open={isOpen} onOpenChange={setIsOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList className="max-h-[60vh] overflow-y-auto">
        <CommandEmpty className="py-12 text-center text-sm text-zinc-500">
          No commands found.
        </CommandEmpty>
        {Object.entries(groupedCommands).map(([group, commands], idx, arr) => (
          <div key={group}>
            <CommandGroup heading={group}>
              {commands.map((cmd) => (
                <CommandItem 
                  key={cmd.id} 
                  command={cmd} 
                  onSelect={handleSelect} 
                />
              ))}
            </CommandGroup>
            {idx < arr.length - 1 && <CommandSeparator />}
          </div>
        ))}
      </CommandList>
    </CommandDialog>
  )
}
