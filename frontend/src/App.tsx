import { RouterProvider } from 'react-router-dom'
import { Suspense } from 'react'
import { router } from '@/routes'
import { FullScreenLoader } from '@/components/feedback/FullScreenLoader'
import { ErrorBoundary } from '@/components/feedback/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<FullScreenLoader />}>
        <RouterProvider router={router} />
      </Suspense>
    </ErrorBoundary>
  )
}

export default App
