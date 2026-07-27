import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { cn } from '@/lib/utils'

export function RightSidebar() {
  const rightSidebarOpen = useWorkspaceStore((state) => state.rightSidebarOpen)

  return (
    <aside
      className={cn(
        "bg-zinc-900 border-l border-zinc-800 overflow-hidden transition-all duration-300 ease-in-out shrink-0 flex flex-col",
        rightSidebarOpen ? "w-64" : "w-0 border-l-0"
      )}
    >
      <div className="p-4 w-64 min-w-[16rem]">
        <h2 className="font-semibold text-sm text-zinc-400 uppercase tracking-wider">Inspector</h2>
      </div>
    </aside>
  )
}
