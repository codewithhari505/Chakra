import React, { useState } from "react";
import Navbar from "./components/Navbar";
import DashboardPage from "./pages/DashboardPage";
import NetworkPage from "./pages/NetworkPage";
import SimulatorPage from "./pages/SimulatorPage";
import TransactionModal from "./components/TransactionModal";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  return (
    <div className="min-h-screen bg-slate-50 text-gray-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "dashboard" && (
          <DashboardPage onSelectTransaction={setSelectedTransaction} />
        )}
        {activeTab === "network" && <NetworkPage />}
        {activeTab === "simulator" && <SimulatorPage />}
      </main>

      {/* Transaction Details & 4-Pillars Modal */}
      {selectedTransaction && (
        <TransactionModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
          onActionSuccess={() => setSelectedTransaction(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>CHAKRA Anti-Money Laundering (AML) AI Engine • Version 1.0.0</div>
          <div>Statutory Alignment: PMLA 2002 §35A • RBI KYC Amendment Directions 2026 • NPCI UPI 50ms Budget</div>
        </div>
      </footer>
    </div>
  );
}
