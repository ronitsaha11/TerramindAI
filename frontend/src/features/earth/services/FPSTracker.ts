export type FPSListener = (fps: number) => void

/**
 * Tracks frames per second using requestAnimationFrame.
 * Calculates a rolling average over the last 1000ms.
 */
export class FPSTracker {
  private _listeners = new Set<FPSListener>()
  private _rafId: number | null = null
  private _frames = 0
  private _lastTime = performance.now()
  private _currentFPS = 0

  /** Start the tracking loop. */
  start(): void {
    if (this._rafId !== null) return
    this._lastTime = performance.now()
    this._frames = 0
    this._loop()
  }

  /** Stop tracking and release the animation frame. */
  stop(): void {
    if (this._rafId !== null) {
      cancelAnimationFrame(this._rafId)
      this._rafId = null
    }
  }

  /** Get the most recently calculated FPS value. */
  getCurrentFPS(): number {
    return this._currentFPS
  }

  /** Register a listener for one-second FPS updates. */
  subscribe(listener: FPSListener): void {
    this._listeners.add(listener)
    // Send immediate initial value
    listener(this._currentFPS)
  }

  /** Unregister a listener. */
  unsubscribe(listener: FPSListener): void {
    this._listeners.delete(listener)
  }

  private _loop = (): void => {
    this._frames++
    const now = performance.now()
    const elapsed = now - this._lastTime

    if (elapsed >= 1000) {
      this._currentFPS = Math.round((this._frames * 1000) / elapsed)
      this._frames = 0
      this._lastTime = now

      for (const listener of this._listeners) {
        listener(this._currentFPS)
      }
    }

    this._rafId = requestAnimationFrame(this._loop)
  }
}
