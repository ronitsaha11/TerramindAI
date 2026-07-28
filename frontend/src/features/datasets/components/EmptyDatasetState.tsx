import { Database, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function EmptyDatasetState() {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-dashed rounded-lg bg-background/50">
      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Database className="w-6 h-6 text-primary" />
      </div>
      <h3 className="text-lg font-semibold mb-2">No Datasets Loaded</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-[200px]">
        Add a geospatial dataset to begin spatial querying and visualization.
      </p>
      <Button variant="outline" className="gap-2" disabled>
        <Plus className="w-4 h-4" />
        Import Dataset
      </Button>
    </div>
  );
}
