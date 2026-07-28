import { useSpatialStore } from '../stores/useSpatialStore';
import { Loader2 } from 'lucide-react';

export function VisibleFeaturesCounter() {
  const { visibleFeaturesCount, isCalculating } = useSpatialStore();

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-background/80 backdrop-blur-sm border rounded-full px-4 py-1.5 shadow-sm flex items-center gap-2 text-sm text-foreground z-10 pointer-events-auto transition-all">
      <span className="font-medium" aria-live="polite">
        {visibleFeaturesCount.toLocaleString()}
      </span>
      <span className="text-muted-foreground">visible features</span>
      
      {isCalculating && (
        <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground ml-1" />
      )}
    </div>
  );
}
