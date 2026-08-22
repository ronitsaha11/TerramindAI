import { useState, useCallback, useMemo } from 'react';
import { DatasetImportController } from '../services/dataset-import-controller';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { NotificationService } from '../../../shared/services/notification.service';
import { useMapStore } from '../../earth/stores/useMapStore';

export function useDatasetImport() {
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isEngineReady = useMapStore((state) => state.isEngineReady);

  const controller = useMemo(() => {
    if (!isEngineReady) return null;
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (!registry) return null;
    return new DatasetImportController(registry);
  }, [isEngineReady]);

  const clearError = useCallback(() => setError(null), []);

  const importFile = useCallback(async (file: File) => {
    if (!controller) {
      setError('System is still initializing. Please wait.');
      return { success: false, error: 'System is still initializing.' };
    }
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
