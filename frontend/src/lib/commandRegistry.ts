import { 
  Layers, 
  CloudRain, 
  Cpu, 
  LineChart, 
  Server,
  PanelLeft,
  PanelRight
} from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { type ComponentType } from 'react'

export type RegistryCommand = {
  id: string
  title: string
  description: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: ComponentType<any>
  group: string
  keywords: string[]
  shortcut?: string
  action: () => void
}

export const commandRegistry: RegistryCommand[] = [
  {
    id: 'open-layers-panel',
    title: 'Open Layers Panel',
    description: 'Toggle the Layers panel in the workspace',
    icon: Layers,
    group: 'Panels',
    keywords: ['layers', 'map', 'data', 'panel'],
    action: () => useWorkspaceStore.getState().togglePanel('layers'),
  },
  {
    id: 'open-weather-panel',
    title: 'Open Weather Panel',
    description: 'Toggle the Weather panel in the workspace',
    icon: CloudRain,
    group: 'Panels',
    keywords: ['weather', 'forecast', 'meteorology', 'panel'],
    action: () => useWorkspaceStore.getState().togglePanel('weather'),
  },
  {
    id: 'open-ai-panel',
    title: 'Open AI Panel',
    description: 'Toggle the AI Assistant panel',
    icon: Cpu,
    group: 'Panels',
    keywords: ['ai', 'assistant', 'chat', 'intelligence', 'panel'],
    action: () => useWorkspaceStore.getState().togglePanel('ai'),
  },
  {
    id: 'open-analytics-panel',
    title: 'Open Analytics Panel',
    description: 'Toggle the Analytics panel',
    icon: LineChart,
    group: 'Panels',
    keywords: ['analytics', 'charts', 'data', 'graphs', 'panel'],
    action: () => useWorkspaceStore.getState().togglePanel('analytics'),
  },
  {
    id: 'open-jobs-panel',
    title: 'Open Jobs Panel',
    description: 'Toggle the Jobs & Tasks panel',
    icon: Server,
    group: 'Panels',
    keywords: ['jobs', 'tasks', 'processing', 'panel'],
    action: () => useWorkspaceStore.getState().togglePanel('jobs'),
  },
  {
    id: 'toggle-left-sidebar',
    title: 'Toggle Left Sidebar',
    description: 'Show or hide the left workspace tools sidebar',
    icon: PanelLeft,
    group: 'Layout',
    keywords: ['sidebar', 'left', 'toggle', 'layout'],
    action: () => useWorkspaceStore.getState().toggleLeftSidebar(),
  },
  {
    id: 'toggle-right-sidebar',
    title: 'Toggle Right Sidebar',
    description: 'Show or hide the right inspector sidebar',
    icon: PanelRight,
    group: 'Layout',
    keywords: ['sidebar', 'right', 'toggle', 'layout', 'inspector'],
    action: () => useWorkspaceStore.getState().toggleRightSidebar(),
  },
]
