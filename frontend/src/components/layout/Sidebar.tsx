import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard, ArrowLeftRight, Users, Bell,
  BriefcaseBusiness, Network, BarChart3, Settings, ShieldAlert,
  Building2, ShieldCheck, Landmark, LogOut, RefreshCw
} from 'lucide-react';
import { useAuth, PORTAL_CONFIGS, PortalType } from '../../context/AuthContext';

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { to: '/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { to: '/accounts', icon: Users, label: 'Accounts' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/investigations', icon: BriefcaseBusiness, label: 'Investigations' },
  { to: '/network', icon: Network, label: 'Network Analysis' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
];

export default function Sidebar() {
  const { portal, user } = useAuth();
  const config = PORTAL_CONFIGS[portal];

  const portalIcons: Record<PortalType, any> = {
    bank: Building2,
    cybersecurity: ShieldCheck,
    rbi: Landmark,
  };
  const PortalIcon = portalIcons[portal];

  return (
    <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0 font-['Inter']">
      {/* Brand & Active Authority */}
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white shrink-0 shadow-sm"
            style={{ backgroundColor: config.primaryColor }}
          >
            <PortalIcon className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-sm text-gray-900 font-['Poppins'] truncate">
              {config.name.replace(' Portal', '').replace(' Reserve Bank of India', 'RBI')}
            </div>
            <div className="text-[10px] text-gray-400 truncate">
              {config.authority.substring(0, 26)}
            </div>
          </div>
        </div>

        <div className="mt-3 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-[10px] text-gray-500 font-mono flex items-center justify-between">
          <span className="truncate">{user?.badge || config.staffCode}</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                isActive
                  ? 'bg-blue-50 text-blue-700 font-semibold border-l-2 border-blue-600 pl-[10px]'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Portal Switcher Quick Action & Bottom */}
      <div className="px-3 py-3 border-t border-gray-100 space-y-1">
        <Link
          to="/login"
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
          <span>Switch Login Portal</span>
        </Link>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
              isActive ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-500 hover:bg-gray-50'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <Settings className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
              Settings
            </>
          )}
        </NavLink>
      </div>
    </aside>
  );
}
