import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { cn } from '@/lib/utils'
import { LeftToolRail } from './LeftToolRail'

export function LeftSidebar() {
  const leftSidebarOpen = useWorkspaceStore((state) => state.leftSidebarOpen)

  return (
    <aside
      className={cn(
        "bg-zinc-900 border-r border-zinc-800 overflow-hidden transition-all duration-300 ease-in-out shrink-0 flex",
        leftSidebarOpen ? "w-64" : "w-12"
      )}
    >
      <LeftToolRail />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="p-4 w-[13rem] min-w-[13rem]">
          <h2 className="font-semibold text-sm text-zinc-400 uppercase tracking-wider">Workspace Tools</h2>
        </div>
      </div>
    </aside>
  )
}
