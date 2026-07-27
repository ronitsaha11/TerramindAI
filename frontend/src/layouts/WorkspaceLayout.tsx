import { TopNav } from '@/components/hud/TopNav'
import { LeftSidebar } from '@/components/workspace/LeftSidebar'
import { RightSidebar } from '@/components/workspace/RightSidebar'
import { MapViewport } from '@/components/workspace/MapViewport'
import { WorkspaceOverlay } from '@/components/workspace/WorkspaceOverlay'
import { CommandPalette } from '@/components/command/CommandPalette'
import { StatusBar } from '@/components/workspace/status/StatusBar'
import { ShortcutManager } from '@/components/workspace/ShortcutManager'

export function WorkspaceLayout() {
  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-zinc-950 text-zinc-50">
      <ShortcutManager />
      <TopNav />
      <div className="flex-1 flex overflow-hidden">
        <LeftSidebar />
        
        <div className="flex-1 relative overflow-hidden flex flex-col">
          <MapViewport />
          <WorkspaceOverlay />
        </div>
        
        <RightSidebar />
      </div>
      <StatusBar />
      <CommandPalette />
    </div>
  )
}

