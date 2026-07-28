import { useEffect } from 'react';
import { useToastStore, type Toast } from '../stores/useToastStore';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AnimatePresence, motion } from 'framer-motion';

function ToastItem({ toast, onRemove }: { toast: Toast, onRemove: (id: string) => void }) {
  useEffect(() => {
    if (toast.duration > 0) {
      const timer = setTimeout(() => {
        onRemove(toast.id);
      }, toast.duration);
      return () => clearTimeout(timer);
    }
  }, [toast, onRemove]);

  const Icon = toast.type === 'success' ? CheckCircle2 :
               toast.type === 'error' ? AlertCircle : Info;

  const colorStyles = toast.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                      toast.type === 'error' ? 'bg-destructive/10 text-destructive border-destructive/20' :
                      'bg-blue-500/10 text-blue-500 border-blue-500/20';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className={`pointer-events-auto flex items-start gap-3 p-3 rounded-lg border shadow-lg backdrop-blur-md min-w-[300px] max-w-[400px] ${colorStyles}`}
      role="alert"
      aria-live="polite"
    >
      <Icon className="w-5 h-5 mt-0.5 shrink-0" />
      <div className="flex-1 font-medium text-sm leading-tight text-foreground">
        {toast.message}
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="w-6 h-6 shrink-0 -mr-1 -mt-1 opacity-70 hover:opacity-100 transition-opacity"
        onClick={() => onRemove(toast.id)}
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </Button>
    </motion.div>
  );
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none items-end">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </AnimatePresence>
    </div>
  );
}
