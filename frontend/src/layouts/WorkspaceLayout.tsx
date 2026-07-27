import { TopNav } from '@/components/hud/TopNav'
import { LeftSidebar } from '@/components/workspace/LeftSidebar'
import { RightSidebar } from '@/components/workspace/RightSidebar'
import { MapViewport } from '@/components/workspace/MapViewport'

export function WorkspaceLayout() {
  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-zinc-950 text-zinc-50">
      <TopNav />
      <div className="flex-1 flex overflow-hidden">
        <LeftSidebar />
        <MapViewport />
        <RightSidebar />
      </div>
    </div>
  )
}
