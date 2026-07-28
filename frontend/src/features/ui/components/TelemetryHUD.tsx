import React from 'react';
import { useTelemetryStore } from '../stores/useTelemetryStore';

export const TelemetryHUD: React.FC = () => {
  const snapshot = useTelemetryStore(state => state.snapshot);

  if (!snapshot) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: 20,
        left: 20,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        color: '#00ffcc',
        padding: '12px',
        borderRadius: '8px',
        fontFamily: 'monospace',
        fontSize: '12px',
        pointerEvents: 'none', // Read-only, no interactions
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(0, 255, 204, 0.2)'
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#fff' }}>Telemetry HUD</div>
      
      <div>LAT: {snapshot.latitude.toFixed(4)}°</div>
      <div>LON: {snapshot.longitude.toFixed(4)}°</div>
      <div>ALT: {Math.round(snapshot.altitude).toLocaleString()} m</div>
      
      <div style={{ marginTop: '8px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
        DATE: {snapshot.simulationDate.toUTCString()}
      </div>
      <div>RATE: {snapshot.simulationRate.toFixed(1)}x</div>
      
      <div style={{ marginTop: '8px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.2)' }}>
        FPS: {Math.round(snapshot.fps)}
      </div>
      <div>FIDELITY: {snapshot.fidelityLevel}</div>
    </div>
  );
};
