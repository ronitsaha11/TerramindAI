import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4 text-zinc-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-zinc-800 mb-4">404</h1>
        <h2 className="text-2xl font-semibold mb-6">Page Not Found</h2>
        <Button onClick={() => navigate('/')} variant="secondary">
          Return Home
        </Button>
      </div>
    </div>
  )
}
