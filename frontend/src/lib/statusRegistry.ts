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

export type StatusPosition = 'left' | 'center' | 'right'

export type RegistryStatusItem = {
  id: string
  label: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: ComponentType<any>
  position: StatusPosition
  formatter: (state: WorkspaceStatusState) => string
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
    label: 'Latitude (from camera)',
    icon: Globe,
    position: 'center',
    formatter: () => {
      const { camera } = useCameraStore.getState()
      const dir = camera.latitude >= 0 ? 'N' : 'S'
      return `${Math.abs(camera.latitude).toFixed(6)}° ${dir}`
    },
    visible: () => true,
  },
  {
    id: 'longitude',
    label: 'Longitude (from camera)',
    icon: Navigation,
    position: 'center',
    formatter: () => {
      const { camera } = useCameraStore.getState()
      const dir = camera.longitude >= 0 ? 'E' : 'W'
      return `${Math.abs(camera.longitude).toFixed(6)}° ${dir}`
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
