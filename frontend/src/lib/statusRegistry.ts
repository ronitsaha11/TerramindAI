import { type ComponentType } from 'react'
import { 
  Activity, 
  Globe, 
  Map, 
  Navigation, 
  Monitor, 
  Wifi, 
  Server, 
  Bell 
} from 'lucide-react'
import { type WorkspaceStatusState } from '@/stores/workspace/useWorkspaceStatusStore'
import { useCameraStore } from '@/features/earth/stores/useCameraStore'
import { useCursorStore } from '@/features/earth/stores/useCursorStore'

export type StatusPosition = 'left' | 'center' | 'right'

export type RegistryStatusItem = {
  id: string
  label: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: ComponentType<any>
  position: StatusPosition
  formatter: (state: WorkspaceStatusState) => string
  colorClass?: (state: WorkspaceStatusState) => string
  visible: (state: WorkspaceStatusState) => boolean
}

export const statusRegistry: RegistryStatusItem[] = [
  {
    id: 'system-status',
    label: 'System Status',
    icon: Activity,
    position: 'left',
    formatter: (state) => state.workspaceStatus,
    visible: () => true,
  },
  {
    id: 'projection',
    label: 'Projection',
    icon: Map,
    position: 'left',
    formatter: (state) => state.projection,
    visible: () => true,
  },
  {
    id: 'latitude',
    label: 'Cursor Latitude',
    icon: Globe,
    position: 'center',
    formatter: () => {
      const { latitude } = useCursorStore.getState()
      const { camera } = useCameraStore.getState()
      const lat = latitude !== null ? latitude : camera.latitude
      const dir = lat >= 0 ? 'N' : 'S'
      return `${Math.abs(lat).toFixed(6)}° ${dir}`
    },
    visible: () => true,
  },
  {
    id: 'longitude',
    label: 'Cursor Longitude',
    icon: Navigation,
    position: 'center',
    formatter: () => {
      const { longitude } = useCursorStore.getState()
      const { camera } = useCameraStore.getState()
      const lng = longitude !== null ? longitude : camera.longitude
      const dir = lng >= 0 ? 'E' : 'W'
      return `${Math.abs(lng).toFixed(6)}° ${dir}`
    },
    visible: () => true,
  },
  {
    id: 'zoom',
    label: 'Zoom Level (from camera)',
    icon: Monitor,
    position: 'right',
    formatter: () => {
      const { camera } = useCameraStore.getState()
      return camera.zoom.toFixed(2)
    },
    visible: () => true,
  },
  {
    id: 'fps',
    label: 'Frames Per Second',
    icon: Activity,
    position: 'right',
    formatter: (state) => state.fps !== null ? state.fps.toFixed(0) : '--',
    colorClass: (state) => {
      if (state.fps === null) return 'text-zinc-400'
      if (state.fps >= 50) return 'text-green-500'
      if (state.fps >= 30) return 'text-yellow-500'
      return 'text-red-500'
    },
    visible: () => true,
  },
  {
    id: 'jobs',
    label: 'Background Jobs',
    icon: Server,
    position: 'right',
    formatter: (state) => state.jobCount.toString(),
    visible: () => true,
  },
  {
    id: 'network',
    label: 'Network Status',
    icon: Wifi,
    position: 'right',
    formatter: (state) => state.networkStatus,
    visible: () => true,
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: Bell,
    position: 'right',
    formatter: (state) => state.notificationCount.toString(),
    visible: () => true,
  }
]
