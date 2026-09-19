import React from "react";

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: "dashboard", label: "Triage Dashboard" },
    { id: "network", label: "Graph Network Explorer" },
    { id: "simulator", label: "Real-Time Transaction Scanner" },
  ];

  return (
    <header className="border-b border-gray-200 bg-white sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-md">
            CH
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-gray-900 text-base">CHAKRA AML</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-mono border border-emerald-200">
                PMLA / RBI 2026 Compliant
              </span>
            </div>
            <p className="text-[11px] text-gray-500">Financial Crime Intelligence &amp; Graph Analytics</p>
          </div>
        </div>

        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold transition ${
                activeTab === item.id
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-medium text-gray-800">Investigator Workspace</div>
            <div className="text-[10px] text-emerald-600 font-mono flex items-center gap-1 justify-end">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              API &amp; Models Active
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
