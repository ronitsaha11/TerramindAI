export const DEFAULT_CHOREOGRAPHY_CONFIG = {
  defaultDurationMs: 3000,
  defaultArcEnabled: true,
  defaultEasing: 'easeInOutCubic'
};

export const DEFAULT_CHOREOGRAPHY_STATE = {
  status: 'idle' as const,
  activeFlight: null,
  progress: 0,
  elapsedTime: 0,
  interruptionReason: 'NONE' as const
};
