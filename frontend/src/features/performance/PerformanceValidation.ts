

export class PerformanceValidation {
  public static validateDeltaMs(deltaMs: number): number {
    // Prevent zero division or excessively large spikes (e.g. tab paused)
    if (deltaMs <= 0) return 16.66; // assume 60fps
    if (deltaMs > 1000) return 1000; // clamp to 1 second
    return deltaMs;
  }
}
