export const RenderingLifecycleState = {
  UNINITIALIZED: 'UNINITIALIZED',
  MOUNTING: 'MOUNTING',
  READY: 'READY',
  ERROR: 'ERROR',
  DESTROYED: 'DESTROYED',
} as const;

export type RenderingLifecycleState = typeof RenderingLifecycleState[keyof typeof RenderingLifecycleState];
