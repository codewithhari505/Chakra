import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Building2,
  ShieldCheck,
  Landmark,
  Mail,
  Lock,
  Eye,
  EyeOff,
  KeyRound,
  Shield,
  CheckCircle2,
  ArrowRight,
  Fingerprint,
  ScanFace,
  Camera,
  Check,
  Sparkles,
  AlertCircle,
  UserCheck,
} from 'lucide-react';
import { useAuth, PortalType, PORTAL_CONFIGS } from '../context/AuthContext';

interface OfficerFaceProfile {
  name: string;
  designation: string;
  badgeId: string;
  clearance: string;
  colorGrad: string;
  avatarInitials: string;
  faceConfidence: string;
  department: string;
}

const OFFICER_FACES: Record<PortalType, OfficerFaceProfile> = {
  bank: {
    name: 'Rohan Sharma',
    designation: 'Principal AML Investigator & Compliance Head',
    badgeId: 'SCB-AML-8921',
    clearance: 'LEVEL 2 - CONFIDENTIAL',
    colorGrad: 'from-blue-600 to-indigo-600',
    avatarInitials: 'RS',
    faceConfidence: '99.4%',
    department: 'Scheduled Commercial Banks AML Operations Unit',
  },
  cybersecurity: {
    name: 'Agent Priya Nair',
    designation: 'Lead Cyber Threat Specialist & Mule Ring Interdictor',
    badgeId: 'SOC-CYBER-409',
    clearance: 'LEVEL 3 - TS/SCI-FCI',
    colorGrad: 'from-orange-500 to-amber-600',
    avatarInitials: 'PN',
    faceConfidence: '99.8%',
    department: 'I4C / CERT-In National Financial Cyber Command',
  },
  rbi: {
    name: 'Director K. V. Subramanian',
    designation: 'Supervisory Director — Enforcement & Regulatory Oversight',
    badgeId: 'RBI-DOS-001',
    clearance: 'LEVEL 4 - STATUTORY EXECUTIVE',
    colorGrad: 'from-emerald-700 to-teal-800',
    avatarInitials: 'KS',
    faceConfidence: '99.9%',
    department: 'Reserve Bank of India — Department of Supervision (DoS)',
  },
};

export default function Login() {
  const { portalType } = useParams<{ portalType?: string }>();
  const navigate = useNavigate();
  const { login } = useAuth();

  const initialPortal: PortalType =
    portalType === 'cybersecurity'
      ? 'cybersecurity'
      : portalType === 'rbi'
      ? 'rbi'
      : 'bank';

  const [activePortal, setActivePortal] = useState<PortalType>(initialPortal);
  const [authMethod, setAuthMethod] = useState<'face' | 'credentials'>('face');
  const [email, setEmail] = useState(PORTAL_CONFIGS[initialPortal].defaultEmail);
  const [password, setPassword] = useState(PORTAL_CONFIGS[initialPortal].defaultPass);
  const [showPassword, setShowPassword] = useState(false);
  const [tokenCode, setTokenCode] = useState('749-012');
  const [rememberMe, setRememberMe] = useState(true);

  // Face scanning state machine
  const [scanStep, setScanStep] = useState<'idle' | 'scanning' | 'verifying' | 'matched'>('idle');
  const [scanMessage, setScanMessage] = useState<string>('');

  useEffect(() => {
    if (portalType && (portalType === 'bank' || portalType === 'cybersecurity' || portalType === 'rbi')) {
      setActivePortal(portalType as PortalType);
      setEmail(PORTAL_CONFIGS[portalType as PortalType].defaultEmail);
      setPassword(PORTAL_CONFIGS[portalType as PortalType].defaultPass);
    }
  }, [portalType]);

  const handlePortalSwitch = (portal: PortalType) => {
    setActivePortal(portal);
    setEmail(PORTAL_CONFIGS[portal].defaultEmail);
    setPassword(PORTAL_CONFIGS[portal].defaultPass);
    setScanStep('idle');
    setScanMessage('');
  };

  const handleFaceScanLogin = () => {
    const officer = OFFICER_FACES[activePortal];
    setScanStep('scanning');
    setScanMessage('Calibrating biometric facial mesh & optical landmarks...');

    setTimeout(() => {
      setScanStep('verifying');
      setScanMessage('PMLA 2002 §35A & RBI 2026 Anti-Spoofing Liveness Verified...');

      setTimeout(() => {
        setScanStep('matched');
        setScanMessage(`Biometric Identity Confirmed (${officer.faceConfidence} Match): ${officer.name}`);

        setTimeout(() => {
          login(activePortal, PORTAL_CONFIGS[activePortal].defaultEmail, officer.name);
          navigate('/dashboard');
        }, 600);
      }, 700);
    }, 800);
  };

  const handleCredentialSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setScanStep('verifying');
    setScanMessage(`Authenticating tokens with ${PORTAL_CONFIGS[activePortal].name}...`);

    setTimeout(() => {
      login(activePortal, email, OFFICER_FACES[activePortal].name);
      navigate('/dashboard');
    }, 600);
  };

  const config = PORTAL_CONFIGS[activePortal];
  const officer = OFFICER_FACES[activePortal];

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-between selection:bg-blue-600 selection:text-white font-['Inter']">
      {/* Top Banner */}
      <header className="px-6 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold font-['Poppins'] shadow-sm">
            CH
          </div>
          <div>
            <div className="text-sm font-bold text-gray-900 font-['Poppins'] tracking-tight">
              CHAKRA AML INVESTIGATION PLATFORM
            </div>
            <div className="text-[11px] text-gray-500">
              National Financial Intelligence &amp; Multi-Agency Biometric Gateway
            </div>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-medium font-mono text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Biometric Gate Active
          </span>
          <span className="text-gray-400 font-mono text-[11px]">PMLA 2002 §35A / RBI KYC 2026</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Portal Selection & Corresponding Face Identity */}
          <div className="lg:col-span-5 space-y-5">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600 font-['Poppins']">
                Multi-Portal Authentication
              </span>
              <h1 className="text-2xl font-bold text-gray-900 font-['Poppins'] mt-1">
                Access by Corresponding Face
              </h1>
              <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                Choose your department below to verify through the designated facial biometric ID or security token. Access to all dashboards is strictly locked until verified.
              </p>
            </div>

            {/* Portal Cards Selector */}
            <div className="space-y-3">
              {[
                {
                  id: 'bank' as PortalType,
                  title: 'Commercial Bank AML',
                  role: 'Officer Rohan Sharma',
                  desc: 'Bank Compliance & STR Filing',
                  icon: Building2,
                  border: activePortal === 'bank' ? 'border-blue-600 bg-blue-50/70 shadow-sm' : 'border-gray-200 bg-white hover:border-blue-200',
                  iconColor: 'text-blue-600 bg-blue-100',
                  initials: 'RS',
                },
                {
                  id: 'cybersecurity' as PortalType,
                  title: 'Cybersecurity & SOC',
                  role: 'Agent Priya Nair',
                  desc: 'Mule Ring Detection & Cyber Threat Intel',
                  icon: ShieldCheck,
                  border: activePortal === 'cybersecurity' ? 'border-orange-500 bg-orange-50/70 shadow-sm' : 'border-gray-200 bg-white hover:border-orange-200',
                  iconColor: 'text-orange-600 bg-orange-100',
                  initials: 'PN',
                },
                {
                  id: 'rbi' as PortalType,
                  title: 'Reserve Bank of India (RBI)',
                  role: 'Director K. V. Subramanian',
                  desc: 'Central Bank Regulatory & PMLA Oversight',
                  icon: Landmark,
                  border: activePortal === 'rbi' ? 'border-emerald-600 bg-emerald-50/70 shadow-sm' : 'border-gray-200 bg-white hover:border-emerald-200',
                  iconColor: 'text-emerald-700 bg-emerald-100',
                  initials: 'KS',
                },
              ].map((item) => {
                const Icon = item.icon;
                const isSelected = activePortal === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handlePortalSwitch(item.id)}
                    className={`w-full p-3.5 rounded-xl border text-left flex items-center gap-3.5 transition-all ${item.border}`}
                  >
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${item.iconColor}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-900 font-['Poppins'] truncate">
                          {item.title}
                        </span>
                        {isSelected && (
                          <span className="text-[10px] uppercase font-bold text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded-full font-mono">
                            Selected
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-medium text-gray-700 mt-0.5">{item.role}</div>
                      <div className="text-[11px] text-gray-400 truncate">{item.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Regulatory Notice */}
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-xl text-[11px] text-gray-500 space-y-1">
              <div className="font-semibold text-gray-700 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-blue-600" />
                Statutory Access Gate
              </div>
              <p>
                Access to investigator data, graphs, and transaction networks requires authentication with the corresponding authority face or token.
              </p>
            </div>
          </div>

          {/* Right Column: Sleek Light Login Card with Face Verification */}
          <div className="lg:col-span-7">
            <div className="bg-white border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
              {/* Top Accent Strip */}
              <div
                className="absolute top-0 left-0 right-0 h-1.5"
                style={{ backgroundColor: config.primaryColor }}
              />

              {/* Portal Header */}
              <div className="flex items-start justify-between gap-3 mb-5">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded-full border ${config.badgeColor}`}>
                      {config.authority}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-gray-900 font-['Poppins']">{config.name}</h2>
                  <p className="text-xs text-gray-500 mt-0.5">{config.subtitle}</p>
                </div>
              </div>

              {/* Auth Method Switcher Tabs (Face Verification vs Credentials) */}
              <div className="flex items-center p-1 bg-gray-100 rounded-xl mb-5 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setAuthMethod('face')}
                  className={`flex-1 py-2 rounded-lg flex items-center justify-center gap-2 transition ${
                    authMethod === 'face'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  <ScanFace className="w-4 h-4 text-blue-600" />
                  <span>Face Biometric ID</span>
                  <span className="text-[9px] bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded font-mono font-bold">1-CLICK</span>
                </button>

                <button
                  type="button"
                  onClick={() => setAuthMethod('credentials')}
                  className={`flex-1 py-2 rounded-lg flex items-center justify-center gap-2 transition ${
                    authMethod === 'credentials'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  <KeyRound className="w-4 h-4 text-gray-500" />
                  <span>Security Token / Password</span>
                </button>
              </div>

              {/* MODE 1: FACE RECOGNITION AUTHENTICATION */}
              {authMethod === 'face' ? (
                <div className="space-y-4">
                  {/* Face Scanner Camera Reticle Viewport */}
                  <div className="relative border-2 border-dashed border-gray-200 rounded-2xl bg-gradient-to-b from-gray-50 to-slate-100 p-6 flex flex-col items-center justify-center text-center overflow-hidden min-h-[260px]">
                    {/* Corner Reticle Markers */}
                    <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-blue-600" />
                    <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-blue-600" />
                    <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-blue-600" />
                    <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-blue-600" />

                    {/* Laser scanning sweep line when scanning */}
                    {scanStep === 'scanning' && (
                      <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse top-1/2 -translate-y-1/2 shadow-lg shadow-blue-500/50" />
                    )}

                    {/* Face Avatar Silhouette with Landmark Rings */}
                    <div className="relative mb-3">
                      <div
                        className={`w-24 h-24 rounded-2xl bg-gradient-to-tr ${officer.colorGrad} flex items-center justify-center text-white text-2xl font-bold font-['Poppins'] shadow-md transition-transform duration-300 ${
                          scanStep === 'scanning' ? 'scale-105 ring-4 ring-blue-400/40' : ''
                        }`}
                      >
                        {officer.avatarInitials}
                      </div>

                      {/* Biometric Status Icon Overlay */}
                      <div className="absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                        {scanStep === 'matched' ? (
                          <Check className="w-4 h-4 text-emerald-600" />
                        ) : scanStep === 'verifying' ? (
                          <Sparkles className="w-4 h-4 text-amber-500 animate-spin" />
                        ) : (
                          <ScanFace className="w-4 h-4 text-blue-600" />
                        )}
                      </div>
                    </div>

                    {/* Corresponding Officer Information */}
                    <div className="space-y-0.5 max-w-sm">
                      <div className="text-sm font-bold text-gray-900 font-['Poppins']">{officer.name}</div>
                      <div className="text-xs text-blue-700 font-semibold">{officer.designation}</div>
                      <div className="text-[11px] text-gray-500">{officer.department}</div>
                    </div>

                    {/* Badge & Clearance pill */}
                    <div className="mt-3 flex items-center gap-2 font-mono text-[10px]">
                      <span className="px-2 py-0.5 rounded bg-white border border-gray-200 text-gray-700 font-semibold">
                        ID: {officer.badgeId}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold">
                        {officer.clearance}
                      </span>
                    </div>

                    {/* Live feedback status message */}
                    {scanMessage && (
                      <div className="mt-3 px-3 py-1.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold flex items-center gap-2">
                        {scanStep === 'matched' ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        )}
                        <span>{scanMessage}</span>
                      </div>
                    )}
                  </div>

                  {/* Face Authentication Action Button */}
                  <button
                    type="button"
                    onClick={handleFaceScanLogin}
                    disabled={scanStep !== 'idle'}
                    className="w-full py-3 px-4 rounded-xl text-white font-semibold text-sm transition shadow-sm flex items-center justify-center gap-2 font-['Poppins'] disabled:opacity-75"
                    style={{ backgroundColor: config.primaryColor }}
                  >
                    {scanStep === 'idle' && (
                      <>
                        <ScanFace className="w-4 h-4" />
                        <span>Verify Face &amp; Enter {config.name}</span>
                      </>
                    )}
                    {scanStep === 'scanning' && 'Scanning Face Landmarks...'}
                    {scanStep === 'verifying' && 'Verifying Anti-Spoofing Liveness...'}
                    {scanStep === 'matched' && 'Access Authorized! Loading Dashboard...'}
                  </button>
                </div>
              ) : (
                /* MODE 2: CREDENTIALS & SECURITY TOKEN FORM */
                <form onSubmit={handleCredentialSubmit} className="space-y-4">
                  {/* Email */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                      Department Email / Officer ID
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="officer@department.gov.in"
                        className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-1 focus:ring-blue-100 transition"
                      />
                    </div>
                  </div>

                  {/* Password with Eye Toggle */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-gray-700">Security Passcode</label>
                      <button
                        type="button"
                        onClick={() => alert('Demo Passcode is prefilled. Click Log In.')}
                        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Reset Passcode
                      </button>
                    </div>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        placeholder="••••••••••••"
                        className="w-full pl-10 pr-10 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-1 focus:ring-blue-100 transition font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Department Specific Token */}
                  {activePortal === 'bank' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                        Bank Branch IFSC &amp; Treasury Code
                      </label>
                      <div className="relative">
                        <Building2 className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          defaultValue="SBIN0001234 — Mumbai Main Treasury"
                          className="w-full pl-10 pr-4 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl text-gray-700 font-mono focus:outline-none"
                        />
                      </div>
                    </div>
                  )}

                  {activePortal === 'cybersecurity' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                        CERT-In Terminal Node &amp; Threat Token
                      </label>
                      <div className="relative">
                        <Fingerprint className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          defaultValue="NODE-I4C-CYBER-09 [TS/SCI Clearance Active]"
                          className="w-full pl-10 pr-4 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl text-gray-700 font-mono focus:outline-none"
                        />
                      </div>
                    </div>
                  )}

                  {activePortal === 'rbi' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                        Department of Supervision (DoS) Token PIN
                      </label>
                      <div className="relative">
                        <KeyRound className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          value={tokenCode}
                          onChange={(e) => setTokenCode(e.target.value)}
                          className="w-full pl-10 pr-4 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl text-gray-700 font-mono focus:outline-none"
                        />
                      </div>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={scanStep === 'verifying'}
                    className="w-full mt-2 py-3 px-4 rounded-xl text-white font-semibold text-sm transition shadow-sm flex items-center justify-center gap-2 font-['Poppins'] disabled:opacity-70"
                    style={{ backgroundColor: config.primaryColor }}
                  >
                    <span>Authenticate &amp; Enter {config.name}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>
              )}

              {/* Quick Jump Buttons for User */}
              <div className="mt-6 pt-5 border-t border-gray-100">
                <div className="text-[11px] text-gray-400 font-semibold uppercase tracking-wider mb-2">
                  Corresponding Agency Face:
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handlePortalSwitch('bank')}
                    className={`py-1.5 px-2 rounded-lg text-xs font-semibold border text-center transition ${
                      activePortal === 'bank'
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    🏦 Bank Face
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePortalSwitch('cybersecurity')}
                    className={`py-1.5 px-2 rounded-lg text-xs font-semibold border text-center transition ${
                      activePortal === 'cybersecurity'
                        ? 'bg-orange-500 text-white border-orange-500'
                        : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    🛡️ Cyber Face
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePortalSwitch('rbi')}
                    className={`py-1.5 px-2 rounded-lg text-xs font-semibold border text-center transition ${
                      activePortal === 'rbi'
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    🏛️ RBI Face
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 border-t border-gray-200 bg-white text-center text-xs text-gray-400 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>CHAKRA Anti-Money Laundering (AML) AI Engine • Version 1.0.0</div>
          <div>Biometric Authentication Framework: PMLA 2002 §35A • RBI KYC Directions 2026 • CERT-In</div>
        </div>
      </footer>
    </div>
  );
}
