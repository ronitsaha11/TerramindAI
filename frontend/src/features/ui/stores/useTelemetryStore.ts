import { create } from 'zustand';
import type { TelemetrySnapshot } from '../models/TelemetrySnapshot';
import type { EarthEngine } from '../../earth/services/EarthEngine';

interface TelemetryStore {
  snapshot: TelemetrySnapshot | null;
  setSnapshot: (snapshot: TelemetrySnapshot) => void;
}

export const useTelemetryStore = create<TelemetryStore>((set) => ({
  snapshot: null,
  setSnapshot: (snapshot) => set({ snapshot }),
}));

// Throttled interval ID
let updateInterval: number | null = null;

export function connectTelemetry(engine: EarthEngine): void {
  disconnectTelemetry(); // Ensure no duplicates
  
  // Throttle updates to 10 FPS (100ms)
  updateInterval = window.setInterval(() => {
    const cameraEngine = engine.getCameraEngine();
    const simulationClock = engine.getSimulationClock();
    const performanceEngine = engine.getPerformanceEngine();

    if (cameraEngine && simulationClock && performanceEngine) {
      const camState = cameraEngine.getState();
      const simState = simulationClock.getState();
      const perfState = performanceEngine.getState();

      useTelemetryStore.getState().setSnapshot({
        latitude: camState.latitude,
        longitude: camState.longitude,
        altitude: camState.altitude,
        simulationDate: new Date(simState.timeMs),
        simulationRate: simState.multiplier,
        fps: perfState.rollingFps,
        fidelityLevel: perfState.fidelityLevel,
      });
    }
  }, 100);
}

export function disconnectTelemetry(): void {
  if (updateInterval !== null) {
    window.clearInterval(updateInterval);
    updateInterval = null;
  }
}
