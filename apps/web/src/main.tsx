import React, { lazy, Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';
import Layout from './components/layout/Layout';
import { ScenarioProvider } from './context/ScenarioContext';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const DevicesPage = lazy(() => import('./pages/DevicesPage'));
const IncidentsPage = lazy(() => import('./pages/IncidentsPage'));
const IncidentDetailPage = lazy(() => import('./pages/IncidentDetailPage'));

const PageFallback = () => (
  <div className="py-12 text-center text-gray-500 text-sm">Loading…</div>
);

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: '#f87171', background: '#030712', minHeight: '100vh' }}>
          <h1>Something went wrong</h1>
          <pre style={{ color: '#9ca3af', marginTop: 16 }}>{this.state.error?.message}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <ScenarioProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route
                path="/"
                element={
                  <Suspense fallback={<PageFallback />}>
                    <Dashboard />
                  </Suspense>
                }
              />
              <Route
                path="/devices"
                element={
                  <Suspense fallback={<PageFallback />}>
                    <DevicesPage />
                  </Suspense>
                }
              />
              <Route
                path="/incidents"
                element={
                  <Suspense fallback={<PageFallback />}>
                    <IncidentsPage />
                  </Suspense>
                }
              />
              <Route
                path="/incidents/:id"
                element={
                  <Suspense fallback={<PageFallback />}>
                    <IncidentDetailPage />
                  </Suspense>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </ScenarioProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);
