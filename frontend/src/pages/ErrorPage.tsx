import { Button } from '@/components/ui/button'
import { useRouteError } from 'react-router-dom'

export function ErrorPage() {
  const error = useRouteError()
  
  console.error("Router error:", error)

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4 text-zinc-50">
      <div className="text-center max-w-md w-full p-8 border border-zinc-800 rounded-lg bg-zinc-900/50">
        <h1 className="text-2xl font-semibold mb-4 text-red-500">Unexpected Error</h1>
        <p className="text-zinc-400 mb-8">
          The application encountered a routing or rendering error.
        </p>
        <Button 
          onClick={() => window.location.href = '/'} 
          variant="secondary"
          className="w-full"
        >
          Reload Application
        </Button>
      </div>
    </div>
  )
}
