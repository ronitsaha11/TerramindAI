import { useToastStore } from '../stores/useToastStore';

class NotificationServiceImpl {
  public success(message: string, duration = 3000): string {
    return useToastStore.getState().addToast({ message, type: 'success', duration });
  }

  public error(message: string, duration = 5000): string {
    return useToastStore.getState().addToast({ message, type: 'error', duration });
  }

  public info(message: string, duration = 3000): string {
    return useToastStore.getState().addToast({ message, type: 'info', duration });
  }

  public remove(id: string): void {
    useToastStore.getState().removeToast(id);
  }
}

export const NotificationService = new NotificationServiceImpl();
