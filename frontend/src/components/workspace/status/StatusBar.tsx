import { useWorkspaceStatusStore } from '@/stores/workspace/useWorkspaceStatusStore'
import { statusRegistry, type StatusPosition } from '@/lib/statusRegistry'
import { StatusItem } from './StatusItem'

export function StatusBar() {
  const state = useWorkspaceStatusStore()

  const renderGroup = (position: StatusPosition) => {
    return statusRegistry
      .filter((item) => item.position === position && item.visible(state))
      .map((item) => (
        <StatusItem
          key={item.id}
          label={item.label}
          value={item.formatter(state)}
          icon={item.icon}
        />
      ))
  }

  return (
    <footer className="h-7 bg-zinc-950 border-t border-zinc-800 flex items-center justify-between px-3 shrink-0 select-none overflow-hidden">
      <div className="flex items-center gap-1 flex-1 justify-start">
        {renderGroup('left')}
      </div>
      <div className="flex items-center gap-3 flex-1 justify-center">
        {renderGroup('center')}
      </div>
      <div className="flex items-center gap-1 flex-1 justify-end">
        {renderGroup('right')}
      </div>
    </footer>
  )
}
