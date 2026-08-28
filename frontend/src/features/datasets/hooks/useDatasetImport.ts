import { useState, useCallback } from 'react';
import { NotificationService } from '../../../shared/services/notification.service';
import { useProjectStore } from '../../../stores/useProjectStore';
import { useQueryClient } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function useDatasetImport() {
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { activeProjectId } = useProjectStore();
  const queryClient = useQueryClient();

  const clearError = useCallback(() => setError(null), []);

  const importFile = useCallback(async (file: File) => {
    if (!activeProjectId) {
      setError('Please select a project first.');
      return { success: false, error: 'No active project' };
    }
    
    setIsImporting(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch(`${API_BASE_URL}/projects/${activeProjectId}/datasets`, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error('Failed to upload dataset.');
      }
      
      const json = await res.json();
      
      NotificationService.success(`Dataset imported successfully`);
      queryClient.invalidateQueries({ queryKey: ['datasets', activeProjectId] });
      return { success: true, data: json.data };
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An error occurred during import.';
      setError(msg);
      return { success: false, error: msg };
    } finally {
      setIsImporting(false);
    }
  }, [activeProjectId, queryClient]);

  return {
    isImporting,
    error,
    clearError,
    importFile,
  };
}
