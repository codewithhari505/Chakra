import React, { createContext, useContext, useState, useEffect } from 'react';

export type PortalType = 'bank' | 'cybersecurity' | 'rbi';

export interface UserSession {
  name: string;
  email: string;
  role: string;
  portal: PortalType;
  institution: string;
  badge: string;
  clearanceLevel: string;
  token: string;
}

export interface PortalConfig {
  id: PortalType;
  name: string;
  subtitle: string;
  authority: string;
  primaryColor: string;
  badgeColor: string;
  defaultEmail: string;
  defaultPass: string;
  staffCode: string;
  description: string;
}

export const PORTAL_CONFIGS: Record<PortalType, PortalConfig> = {
  bank: {
    id: 'bank',
    name: 'Commercial Bank AML Portal',
    subtitle: 'Scheduled Commercial Bank AML Triage & STR Submission',
    authority: 'State Bank & Scheduled Commercial Banking Network',
    primaryColor: '#2563EB',
    badgeColor: 'bg-blue-50 text-blue-700 border-blue-200',
    defaultEmail: 'aml_officer@sbi.co.in',
    defaultPass: 'BankAML#2026',
    staffCode: 'SCB-AML-8921',
    description: 'Operational transaction monitoring, customer KYC profiles, suspicious transaction reporting (STR), and branch-level EDD investigations.',
  },
  cybersecurity: {
    id: 'cybersecurity',
    name: 'Cyber Threat Intelligence SOC',
    subtitle: 'Financial Cyber Crime & Coordinated Mule Ring Interdiction',
    authority: 'I4C / CERT-In National Cyber Intelligence Unit',
    primaryColor: '#F97316',
    badgeColor: 'bg-orange-50 text-orange-700 border-orange-200',
    defaultEmail: 'soc_analyst@cert-in.org.in',
    defaultPass: 'CyberOps#2026',
    staffCode: 'SOC-CYBER-409',
    description: 'Cyber telemetry, device ID cloning, synthetic identity detection, rapid transaction velocity bursts, and automated mule network freezing.',
  },
  rbi: {
    id: 'rbi',
    name: 'RBI Central Regulatory Oversight',
    subtitle: 'Reserve Bank of India • Department of Supervision (DoS)',
    authority: 'Statutory Regulator — PMLA 2002 & Banking Regulation Act',
    primaryColor: '#059669',
    badgeColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    defaultEmail: 'director.supervision@rbi.org.in',
    defaultPass: 'RbiPmla#2026',
    staffCode: 'RBI-DOS-001',
    description: 'Macro-prudential AML surveillance, inter-bank money laundering flows, PMLA §35A regulatory enforcement, and supervisory compliance auditing.',
  },
};

interface AuthContextType {
  user: UserSession | null;
  portal: PortalType;
  login: (portal: PortalType, email: string, name?: string) => void;
  logout: () => void;
  switchPortal: (portal: PortalType) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'chakra_aml_session';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(() => {
    try {
      // Purge any stale legacy localStorage session so login page is always shown first
      localStorage.removeItem(STORAGE_KEY);
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error('Failed to parse saved session', e);
    }
    return null;
  });

  useEffect(() => {
    if (user) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [user]);

  const login = (portalType: PortalType, email: string, name?: string) => {
    const config = PORTAL_CONFIGS[portalType];
    const roles: Record<PortalType, string> = {
      bank: 'Principal AML Investigator',
      cybersecurity: 'Lead Cyber Threat Specialist',
      rbi: 'Supervisory Director',
    };
    const clearances: Record<PortalType, string> = {
      bank: 'LEVEL 2 - CONFIDENTIAL',
      cybersecurity: 'LEVEL 3 - TS/SCI-FCI',
      rbi: 'LEVEL 4 - STATUTORY EXECUTIVE',
    };
    const newUser: UserSession = {
      name: name || (email.split('@')[0].replace(/[._]/g, ' ').toUpperCase()),
      email,
      role: roles[portalType],
      portal: portalType,
      institution: config.name,
      badge: config.staffCode,
      clearanceLevel: clearances[portalType],
      token: `mock_jwt_${portalType}_session_${Date.now()}`,
    };
    setUser(newUser);
  };

  const logout = () => {
    setUser(null);
  };

  const switchPortal = (newPortal: PortalType) => {
    const config = PORTAL_CONFIGS[newPortal];
    login(newPortal, config.defaultEmail);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        portal: user?.portal || 'bank',
        login,
        logout,
        switchPortal,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
