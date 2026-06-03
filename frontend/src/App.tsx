import { Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import AllJobsPage from './pages/AllJobsPage'
import FeaturedPage from './pages/FeaturedPage'
import ApplicationsPage from './pages/ApplicationsPage'
import ResumePage from './pages/ResumePage'
import JobDetailPage from './pages/JobDetailPage'
import ResumeOptimizerPage from './pages/ResumeOptimizerPage'
import { ToastProvider } from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'

export default function App() {
  return (
    <ToastProvider>
      <div className="min-h-screen bg-[#0B1120]">
        <Header />
        <main className="max-w-7xl mx-auto px-4 py-6">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Navigate to="/all" replace />} />
              <Route path="/all" element={<AllJobsPage />} />
              <Route path="/featured" element={<FeaturedPage />} />
              <Route path="/applications" element={<ApplicationsPage />} />
              <Route path="/resume" element={<ResumePage />} />
              <Route path="/jobs/:id" element={<JobDetailPage />} />
              <Route path="/optimizer/:id" element={<ResumeOptimizerPage />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </ToastProvider>
  )
}
