import { useDatasetManager } from '../hooks/useDatasetManager';
import { DatasetListItem } from './DatasetListItem';
import { EmptyDatasetState } from './EmptyDatasetState';
import { DatasetUploader } from './DatasetUploader';

export function DatasetManagerPanel() {
  const { datasets, removeDataset, toggleVisibility } = useDatasetManager();

  return (
    <div className="flex flex-col h-full w-full bg-background border-l">
      <div className="p-4 border-b">
        <h2 className="text-sm font-semibold tracking-tight uppercase text-muted-foreground mb-4">
          Dataset Manager
        </h2>
        <DatasetUploader />
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {datasets.length === 0 ? (
          <EmptyDatasetState />
        ) : (
          datasets.map((dataset) => (
            <DatasetListItem
              key={dataset.id}
              dataset={dataset}
              onRemove={removeDataset}
              onToggleVisibility={toggleVisibility}
            />
          ))
        )}
      </div>
    </div>
  );
}
