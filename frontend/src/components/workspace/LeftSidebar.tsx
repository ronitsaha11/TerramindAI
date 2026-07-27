import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { cn } from '@/lib/utils'

export function LeftSidebar() {
  const leftSidebarOpen = useWorkspaceStore((state) => state.leftSidebarOpen)

  return (
    <aside
      className={cn(
        "bg-zinc-900 border-r border-zinc-800 overflow-hidden transition-all duration-300 ease-in-out shrink-0 flex flex-col",
        leftSidebarOpen ? "w-64" : "w-0 border-r-0"
      )}
    >
      <div className="p-4 w-64 min-w-[16rem]">
        <h2 className="font-semibold text-sm text-zinc-400 uppercase tracking-wider">Workspace Tools</h2>
      </div>
    </aside>
  )
}
