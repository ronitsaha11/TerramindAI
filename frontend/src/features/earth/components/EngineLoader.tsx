import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useMapStore } from '../stores/useMapStore'
import { fadeMotion, defaultTransition } from '@/lib/animations/motionPresets'

export function EngineLoader() {
  const engineState = useMapStore(state => state.engineState)
  const shouldReduceMotion = useReducedMotion()

  const isLoading = engineState !== 'ready'

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          key="engine-loader"
          variants={shouldReduceMotion ? {} : fadeMotion}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={defaultTransition}
          className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950 z-20 select-none"
          aria-label="Loading Earth Engine"
        >
          <div className="flex flex-col items-center gap-4">
            <div className="h-8 w-8 rounded-full border-2 border-zinc-700 border-t-zinc-400 animate-spin" />
            <p className="text-zinc-500 text-xs uppercase tracking-widest font-medium">
              {engineState === 'mounting' ? 'Initializing Engine' : 'Loading'}
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
