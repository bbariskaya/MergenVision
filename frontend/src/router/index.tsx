import { createBrowserRouter } from 'react-router-dom'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import { AuditLogPage } from '@/pages/AuditLogPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { IdentifyPage } from '@/pages/IdentifyPage'
import { IdentificationRequestDetailPage } from '@/pages/IdentificationRequestDetailPage'
import { IdentificationRequestsPage } from '@/pages/IdentificationRequestsPage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { PeoplePage } from '@/pages/PeoplePage'
import { PersonDetailPage } from '@/pages/PersonDetailPage'
import { PersonPhotosPage } from '@/pages/PersonPhotosPage'
import { SystemHealthPage } from '@/pages/SystemHealthPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: '/', element: <DashboardPage /> },
          { path: '/people', element: <PeoplePage /> },
          { path: '/people/:personId', element: <PersonDetailPage /> },
          { path: '/people/:personId/photos', element: <PersonPhotosPage /> },
          { path: '/identify', element: <IdentifyPage /> },
          {
            path: '/identification-requests',
            element: <IdentificationRequestsPage />,
          },
          {
            path: '/identification-requests/:requestId',
            element: <IdentificationRequestDetailPage />,
          },
          { path: '/audit', element: <AuditLogPage /> },
          { path: '/health', element: <SystemHealthPage /> },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
