import { createBrowserRouter } from 'react-router-dom'
import { lazyImport } from '@/lib/lazy'
import { ErrorPage } from '@/pages/ErrorPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { validateEnv } from '@/config/validateEnv'

// Validate environment variables on startup
validateEnv()

// Lazy load the HomePage
const HomePage = lazyImport(() => import('@/pages/HomePage'), 'HomePage')

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
    errorElement: <ErrorPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
