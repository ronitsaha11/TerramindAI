import { Eye, EyeOff, Trash2, Map } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import type { IDataset } from '../../../core/datasets/models/dataset';

interface DatasetListItemProps {
  dataset: IDataset;
  onToggleVisibility: (id: string) => void;
  onRemove: (id: string) => void;
}

export function DatasetListItem({ dataset, onToggleVisibility, onRemove }: DatasetListItemProps) {
  // Use the layer store to get accurate reactive visibility state
  const isVisible = useLayerStore((state) => 
    state.layers.find((l) => l.id === dataset.id)?.visible ?? false
  );

  // `data` is generic on IDataset; only its feature list matters here.
  const rawData = dataset.data as { features?: unknown[] } | null | undefined;
  const featureCount = Array.isArray(rawData?.features)
    ? rawData.features.length
    : (dataset.metadata?.featureCount ?? 0);

  return (
    <div className="flex flex-col gap-2 p-3 rounded-md bg-card border shadow-sm transition-colors hover:bg-accent/50">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          <Map className="w-4 h-4 text-primary shrink-0 mt-0.5" />
          <div className="flex flex-col truncate">
            <span className="text-sm font-medium truncate" title={dataset.name}>
              {dataset.name}
            </span>
            <span className="text-xs text-muted-foreground uppercase">
              {dataset.type}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="w-8 h-8"
            onClick={() => onToggleVisibility(dataset.id)}
            aria-label={isVisible ? 'Hide dataset' : 'Show dataset'}
          >
            {isVisible ? (
              <Eye className="w-4 h-4 text-muted-foreground" />
            ) : (
              <EyeOff className="w-4 h-4 text-muted-foreground opacity-50" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="w-8 h-8 text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={() => onRemove(dataset.id)}
            aria-label="Remove dataset"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      <div className="flex items-center justify-between mt-1 text-xs text-muted-foreground">
        <span>{featureCount.toLocaleString()} features</span>
        <span>
          {dataset.updatedAt 
            ? new Date(dataset.updatedAt).toLocaleDateString() 
            : 'Unknown date'}
        </span>
      </div>
    </div>
  );
}
