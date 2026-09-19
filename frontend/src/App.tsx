import React, { Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import { LoadingSpinner } from './components/common/LoadingState';
import { AuthProvider, useAuth } from './context/AuthContext';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import TransactionDetails from './pages/TransactionDetails';
import Accounts from './pages/Accounts';
import AccountDetails from './pages/AccountDetails';
import Alerts from './pages/Alerts';
import AlertDetails from './pages/AlertDetails';
import Investigations from './pages/Investigations';
import NetworkAnalysis from './pages/NetworkAnalysis';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

function ProtectedLayout() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC]">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/transactions/:id" element={<TransactionDetails />} />
              <Route path="/accounts" element={<Accounts />} />
              <Route path="/accounts/:id" element={<AccountDetails />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/alerts/:id" element={<AlertDetails />} />
              <Route path="/investigations" element={<Investigations />} />
              <Route path="/network" element={<NetworkAnalysis />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/login/:portalType" element={<Login />} />
        <Route path="/*" element={<ProtectedLayout />} />
      </Routes>
    </AuthProvider>
  );
}
