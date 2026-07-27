import { type Variants } from 'framer-motion'

export const workspacePanelMotion: Variants = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 10
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 10
  }
}

export const fadeMotion: Variants = {
  initial: {
    opacity: 0
  },
  animate: {
    opacity: 1
  },
  exit: {
    opacity: 0
  }
}

export const defaultTransition = {
  duration: 0.2,
  ease: 'easeOut' as const
}
