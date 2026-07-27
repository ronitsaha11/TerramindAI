import { Button } from '@/components/ui/button'

type ErrorFallbackProps = {
  error: Error
  resetErrorBoundary: () => void
}

export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  const isDev = import.meta.env.DEV

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4 text-zinc-50">
      <div className="max-w-xl w-full border border-red-900/50 bg-red-950/20 p-6 rounded-lg">
        <h1 className="text-xl font-semibold text-red-500 mb-4">
          {isDev ? "Unexpected Error (Development)" : "Something went wrong"}
        </h1>
        
        {isDev ? (
          <div className="mb-6">
            <p className="font-mono text-sm text-red-400 mb-2 break-words">
              {error.message}
            </p>
            <pre className="font-mono text-xs text-red-300/80 bg-black/40 p-4 rounded overflow-auto max-h-64 whitespace-pre-wrap">
              {error.stack}
            </pre>
          </div>
        ) : (
          <p className="text-zinc-400 mb-6">
            We've encountered an unexpected error. Please try reloading the application.
          </p>
        )}

        <Button 
          variant={isDev ? "destructive" : "default"} 
          onClick={resetErrorBoundary}
        >
          {isDev ? "Retry" : "Reload Application"}
        </Button>
      </div>
    </div>
  )
}
