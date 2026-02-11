import React from 'react';

interface DashboardWidgetProps {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    className?: string;
}

export function DashboardWidget({ title, subtitle, children, className = "" }: DashboardWidgetProps) {
    return (
        <div className={`rounded-xl border border-gray-100 bg-white p-6 shadow-sm flex flex-col ${className}`}>
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
                    {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
                </div>
            </div>
            <div className="flex-1">
                {children}
            </div>
        </div>
    );
}
