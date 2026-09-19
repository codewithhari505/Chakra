import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Search, Bell, ChevronDown, User, LogOut, RefreshCw, Building2, ShieldCheck, Landmark } from 'lucide-react';
import { getHealth } from '../../services/analyticsService';
import { useAuth, PORTAL_CONFIGS, PortalType } from '../../context/AuthContext';

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'AML Investigation Overview',
  '/transactions': 'Transactions',
  '/accounts': 'Accounts',
  '/alerts': 'Alerts',
  '/investigations': 'Investigations',
  '/network': 'Network Analysis',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, portal, logout, switchPortal } = useAuth();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [search, setSearch] = useState('');
  const [showProfile, setShowProfile] = useState(false);

  const title = Object.entries(PAGE_TITLES).find(([path]) =>
    location.pathname.startsWith(path.split('/:')[0])
  )?.[1] ?? 'AML Intelligence';

  useEffect(() => {
    getHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
    const t = setInterval(() => {
      getHealth().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
    }, 30000);
    return () => clearInterval(t);
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = search.trim();
    if (!q) return;
    if (q.startsWith('TXN_') || q.startsWith('TX')) navigate(`/transactions/${q}`);
    else if (q.startsWith('ACC')) navigate(`/accounts/${q}`);
    else if (q.startsWith('ALT') || q.startsWith('ALERT')) navigate(`/alerts/${q}`);
    else navigate(`/transactions?q=${encodeURIComponent(q)}`);
    setSearch('');
  }

  const portalConfig = PORTAL_CONFIGS[portal];
  const portalIcons: Record<PortalType, any> = {
    bank: Building2,
    cybersecurity: ShieldCheck,
    rbi: Landmark,
  };
  const PortalIcon = portalIcons[portal];

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-6 gap-4 shrink-0 z-30 font-['Inter']">
      {/* Page Title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-base font-semibold text-gray-900 font-['Poppins'] truncate">{title}</h1>
      </div>

      {/* Active Agency Portal Badge */}
      <div className="hidden lg:flex items-center gap-2">
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${portalConfig.badgeColor}`}>
          <PortalIcon className="w-3.5 h-3.5" />
          <span>{portalConfig.name}</span>
        </div>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="relative w-64 hidden md:block">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search TXN, ACC, ALT..."
          className="w-full pl-9 pr-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100 font-['Inter']"
        />
      </form>

      {/* API Status */}
      <div className="flex items-center gap-1.5 text-xs font-['Inter']">
        <span className={`w-2 h-2 rounded-full ${apiOnline === true ? 'bg-green-500' : apiOnline === false ? 'bg-red-500' : 'bg-gray-300 animate-pulse'}`} />
        <span className={`hidden sm:block ${apiOnline === true ? 'text-green-600' : apiOnline === false ? 'text-red-500' : 'text-gray-400'}`}>
          {apiOnline === true ? 'API Connected' : apiOnline === false ? 'API Offline' : 'Checking...'}
        </span>
      </div>

      {/* Notifications */}
      <button className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition">
        <Bell className="w-4 h-4" />
        <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-orange-500 rounded-full" />
      </button>

      {/* User & Portal Switcher Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowProfile(!showProfile)}
          className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition text-sm font-['Inter']"
        >
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-white"
            style={{ backgroundColor: portalConfig.primaryColor }}
          >
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-gray-800 truncate max-w-[120px]">{user?.name || 'AML Analyst'}</div>
            <div className="text-[10px] text-gray-400 truncate max-w-[120px]">{user?.role || 'Investigator'}</div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
        </button>

        {showProfile && (
          <div className="absolute right-0 top-full mt-1 w-64 bg-white border border-gray-200 rounded-xl shadow-lg py-2 z-50 font-['Inter'] text-sm">
            {/* Header in dropdown */}
            <div className="px-4 py-2 border-b border-gray-100">
              <div className="font-semibold text-xs text-gray-900">{user?.name}</div>
              <div className="text-[11px] text-gray-400">{user?.email}</div>
              <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 w-fit font-mono">
                {user?.clearanceLevel}
              </div>
            </div>

            {/* Portal Switcher Options */}
            <div className="px-2 py-2 border-b border-gray-100">
              <div className="px-2 text-[10px] uppercase font-bold text-gray-400 tracking-wider mb-1">
                Switch Authority Portal:
              </div>
              {[
                { id: 'bank' as PortalType, name: 'Bank AML Portal', icon: Building2 },
                { id: 'cybersecurity' as PortalType, name: 'Cyber Threat SOC', icon: ShieldCheck },
                { id: 'rbi' as PortalType, name: 'RBI Central Oversight', icon: Landmark },
              ].map((p) => {
                const Icon = p.icon;
                const isCurrent = portal === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => {
                      switchPortal(p.id);
                      setShowProfile(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition ${
                      isCurrent
                        ? 'bg-blue-50 text-blue-700 font-semibold'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Icon className="w-3.5 h-3.5 text-gray-500" />
                      {p.name}
                    </span>
                    {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                  </button>
                );
              })}
            </div>

            {/* Standard actions */}
            <div className="pt-1">
              <Link
                to="/settings"
                onClick={() => setShowProfile(false)}
                className="block px-4 py-1.5 text-xs text-gray-700 hover:bg-gray-50 transition"
              >
                System Settings
              </Link>
              <button
                onClick={() => {
                  logout();
                  setShowProfile(false);
                  navigate('/login');
                }}
                className="w-full text-left px-4 py-1.5 text-xs text-red-600 hover:bg-red-50 flex items-center gap-1.5 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out / Exit Portal
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
