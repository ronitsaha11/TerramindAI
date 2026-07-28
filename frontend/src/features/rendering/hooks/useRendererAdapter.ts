import { useEffect } from 'react';
import { DeckGLRendererAdapter } from '../adapters/DeckGLRendererAdapter';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { RenderingLifecycleState } from '../RenderingLifecycle';

export function useRendererAdapter(containerRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const engine = EarthEngine.getInstance();
    
    // Ensure the domain engines (Clock, Camera, Coordinator) are initialized
    engine.initialize();

    const coordinator = engine.getRenderingCoordinator();
    const cameraEngine = engine.getCameraEngine();
    const streamingEngine = engine.getStreamingEngine();
    const terrainEngine = engine.getTerrainEngine();
    const oceanSystem = engine.getOceanSystem();

    if (!coordinator || !cameraEngine || !streamingEngine || !terrainEngine || !oceanSystem) {
      console.error('[useRendererAdapter] EarthEngine systems not properly initialized.');
      return;
    }

    // Only attach if we aren't already initialized
    if (coordinator.getLifecycleState() === RenderingLifecycleState.UNINITIALIZED) {
      const adapter = new DeckGLRendererAdapter(
        container,
        cameraEngine,
        streamingEngine,
        terrainEngine,
        oceanSystem
      );
      coordinator.attachAdapter(adapter);
      coordinator.start();
    }

    return () => {
      // In a real app we might destroy the coordinator, but since EarthEngine lives across re-renders,
      // destroying it here might break HMR. However, following strict lifecycle, we should clean up the coordinator.
      // For now, we rely on EarthEngine.destroy() on top-level unmount.
    };
  }, [containerRef]);
}
