import { useState, useCallback, useMemo } from 'react';
import { DatasetImportController } from '../services/dataset-import-controller';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { NotificationService } from '../../../shared/services/notification.service';

export function useDatasetImport() {
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const controller = useMemo(() => {
    // Note: EarthEngine guarantees getDatasetRegistry() will return the instance
    // once initialization has passed. The UI is generally mounted after EarthEngine is ready.
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (!registry) {
      throw new Error('Dataset registry is not initialized.');
    }
    return new DatasetImportController(registry);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const importFile = useCallback(async (file: File) => {
    setIsImporting(true);
    setError(null);
    try {
      const result = await controller.importFile(file);
      if (!result.success && result.error) {
        setError(result.error);
      } else if (result.success) {
        NotificationService.success(`Dataset imported successfully`);
      }
      return result;
    } finally {
      setIsImporting(false);
    }
  }, [controller]);

  return {
    isImporting,
    error,
    clearError,
    importFile,
  };
}
