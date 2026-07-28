import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { UploadCloud, AlertCircle, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDatasetImport } from '../hooks/useDatasetImport';

export function DatasetUploader() {
  const { importFile, isImporting, error, clearError } = useDatasetImport();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    if (!file) return;
    await importFile(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      void processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      void processFile(e.target.files[0]);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center transition-colors cursor-pointer
          ${isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-muted-foreground/50 hover:bg-accent/50'}
          ${isImporting ? 'opacity-50 pointer-events-none' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".json,.geojson"
          className="hidden"
        />
        
        {isImporting ? (
          <>
            <Loader2 className="w-8 h-8 mb-3 text-primary animate-spin" />
            <h3 className="font-medium text-sm">Importing dataset...</h3>
            <p className="text-xs text-muted-foreground mt-1">This may take a moment</p>
          </>
        ) : (
          <>
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <UploadCloud className="w-5 h-5 text-primary" />
            </div>
            <h3 className="font-medium text-sm">Upload GeoJSON</h3>
            <p className="text-xs text-muted-foreground mt-1 px-4">
              Drag & drop a file here, or click to browse
            </p>
            <p className="text-[10px] text-muted-foreground/70 mt-2 font-mono">
              .geojson, .json
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-2 p-3 text-sm text-destructive-foreground bg-destructive/10 border border-destructive/20 rounded-md relative">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-destructive" />
          <div className="flex-1 text-destructive font-medium leading-tight">
            {error}
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="w-5 h-5 shrink-0 text-destructive hover:bg-destructive/20 absolute top-2 right-2"
            onClick={clearError}
            aria-label="Clear error"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      )}
    </div>
  );
}
