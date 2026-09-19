import React from 'react';

interface Props {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export default function PageHeader({ title, subtitle, actions }: Props) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 font-['Poppins']">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5 font-['Inter']">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
