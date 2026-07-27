import { type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { X } from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace/useWorkspaceStore'
import { motion, useReducedMotion } from 'framer-motion'
import { workspacePanelMotion, defaultTransition } from '@/lib/animations/motionPresets'

type WorkspacePanelProps = {
  id: string
  title: string
  children: ReactNode
}

export function WorkspacePanel({ id, title, children }: WorkspacePanelProps) {
  const closePanel = useWorkspaceStore(state => state.closePanel)
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div 
      variants={shouldReduceMotion ? {} : workspacePanelMotion}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={defaultTransition}
      className="flex flex-col bg-zinc-950 border border-zinc-800 rounded-md shadow-xl w-80 h-96 pointer-events-auto shrink-0"
    >
      <div className="flex items-center justify-between p-3 border-b border-zinc-800 shrink-0">
        <h3 className="font-medium text-sm text-zinc-100">{title}</h3>
        <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400 hover:text-zinc-50" onClick={() => closePanel(id)}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 p-4 overflow-auto text-zinc-400 text-sm">
        {children}
      </div>
    </motion.div>
  )
}

