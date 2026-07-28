import { useRef } from 'react';
import { useRendererAdapter } from '../hooks/useRendererAdapter';

export function LivingEarthViewport() {
  const containerRef = useRef<HTMLDivElement>(null);

  // Attaches the DeckGLRendererAdapter to the container and starts the coordinator
  useRendererAdapter(containerRef);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full bg-zinc-950"
      aria-label="Living Earth Rendering Viewport"
      style={{ position: 'relative' }} // ensure absolute children like deck.gl canvas are contained
    />
  );
}
