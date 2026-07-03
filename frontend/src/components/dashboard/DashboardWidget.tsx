import React from "react";
import { cn } from "@/lib/utils";

interface DashboardWidgetProps {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    className?: string;
    action?: React.ReactNode;
    noPadding?: boolean;
}

export function DashboardWidget({
    title,
    subtitle,
    children,
    className = "",
    action,
    noPadding = false,
}: DashboardWidgetProps) {
    return (
        <div
            className={cn(
                "bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden flex flex-col",
                className
            )}
        >
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-50 flex items-center justify-between flex-shrink-0">
                <div>
                    <h2 className="text-[15px] font-semibold text-slate-900">{title}</h2>
                    {subtitle && (
                        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
                    )}
                </div>
                {action && <div className="flex-shrink-0">{action}</div>}
            </div>

            {/* Body */}
            <div className={cn("flex-1", !noPadding && "p-6")}>
                {children}
            </div>
        </div>
    );
}
