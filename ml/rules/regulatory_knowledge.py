"""
Regulatory Knowledge & Cybersecurity Compliance Standards.

Integrates:
  1. Reserve Bank of India (RBI) Know Your Customer (KYC) Amendment Directions, 2026:
     - Commercial Banks
     - Small Finance Banks (SFBs)
     - Regional Rural Banks (RRBs)
     - Urban Co-operative Banks (UCBs)
     - Rural Co-operative Banks (RCBs)
     - Local Area Banks (LABs)
     Under Section 35A of Banking Regulation Act 1949, PMLA 2002, and PML Rules 2005 Rule 9(14).
  2. Prevention of Money Laundering Act (PMLA), 2002 & PML (Maintenance of Records) Rules, 2005.
  3. Foreign Exchange Management Act (FEMA), 1999 & FEMA 5(R) (Deposit Regulations).
  4. Core Cybersecurity Dataset & Governance Standards (Anonymization, Access Control, Logging & Monitoring).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass(frozen=True)
class AuthorizedCertifyingAuthority:
    """
    Authorized officials for certifying Officially Valid Documents (OVD)
    for NRIs, PIOs, and Foreign Portfolio Investors (FPIs) under RBI 2026 KYC Amendment Directions.
    """
    code: str
    description: str


RBI_2026_AUTHORIZED_CERTIFIERS: List[AuthorizedCertifyingAuthority] = [
    AuthorizedCertifyingAuthority("OVERSEAS_BRANCH_SCB", "Authorised officials of overseas branches of Scheduled Commercial Banks registered in India"),
    AuthorizedCertifyingAuthority("CORRESPONDENT_BANK", "Branches of overseas banks with whom Indian banks have relationships"),
    AuthorizedCertifyingAuthority("NOTARY_PUBLIC_ABROAD", "Notary Public abroad"),
    AuthorizedCertifyingAuthority("COURT_MAGISTRATE", "Court Magistrate abroad"),
    AuthorizedCertifyingAuthority("JUDGE", "Judge of overseas competent jurisdiction"),
    AuthorizedCertifyingAuthority("EMBASSY_CONSULATE", "Indian Embassy / Consulate General in the country where the non-resident customer resides")
]

# Statutory and Regulatory Reference Codes
REGULATORY_FRAMEWORKS = {
    "PMLA_2002": "Prevention of Money Laundering Act, 2002",
    "PML_RULES_2005": "Prevention of Money-Laundering (Maintenance of Records) Rules, 2005 (Rule 9(14))",
    "BRA_1949": "Banking Regulation Act, 1949 (Section 35A)",
    "FEMA_1999": "Foreign Exchange Management Act, 1999 (Section 11(1))",
    "FEMA_5R": "Foreign Exchange Management (Deposit) Regulations, 2016 {FEMA 5(R)}",
    "PSS_2007": "Payment and Settlement Systems Act, 2007 (Section 10(2) r/w Section 18)",
    "RBI_KYC_2026_COMMERCIAL": "RBI (Commercial Banks - Know Your Customer) Amendment Directions, 2026",
    "RBI_KYC_2026_SFB": "RBI (Small Finance Banks - Know Your Customer) Amendment Directions, 2026",
    "RBI_KYC_2026_RRB": "RBI (Regional Rural Banks - Know Your Customer) Amendment Directions, 2026",
    "RBI_KYC_2026_UCB": "RBI (Urban Co-operative Banks - Know Your Customer) Amendment Directions, 2026",
    "RBI_KYC_2026_RCB": "RBI (Rural Co-operative Banks - Know Your Customer) Amendment Directions, 2026",
    "RBI_KYC_2026_LAB": "RBI (Local Area Banks - Know Your Customer) Amendment Directions, 2026",
}

# Cybersecurity Dataset Governance Rules
CYBERSECURITY_RULES = {
    "RULE_1_ANONYMIZATION": "Strip or tokenize PII, internal IP addresses, and customer secrets before sharing.",
    "RULE_2_COMPLIANCE": "Adhere to GDPR and local digital personal data protection mandates.",
    "RULE_3_ACCURATE_LABELING": "Document and distinctly label normal baseline logs vs malicious attack events.",
    "RULE_4_ACCESS_CONTROL": "Enforce Role-Based Access Control (RBAC) on security metrics and datasets.",
    "RULE_5_RETENTION_LIMITS": "Enforce data retention lifecycle policies and purge unneeded historical records.",
}

# 10 Steps to Cybersecurity Architecture Mapping
CYBERSECURITY_TEN_STEPS = {
    1: "Risk management",
    2: "Engagement and training",
    3: "Asset management",
    4: "Architecture and configuration",
    5: "Vulnerability management",
    6: "Identity and access management (IAM)",
    7: "Data security",
    8: "Logging and monitoring",
    9: "Incident management",
    10: "Supply chain security"
}

# Jurisdictions requiring enhanced cross-border KYC certification
CROSS_BORDER_HIGH_RISK_JURISDICTIONS: Set[str] = {
    "DUBAI", "SINGAPORE", "ZURICH", "CAYMAN", "PANAMA", "CYPRUS", "BRITISH VIRGIN ISLANDS"
}
