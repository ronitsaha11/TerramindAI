export interface TelemetrySnapshot {
  latitude: number;
  longitude: number;
  altitude: number;
  simulationDate: Date;
  simulationRate: number;
  fps: number;
  fidelityLevel: string;
}
