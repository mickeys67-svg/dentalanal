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
                "bg-card rounded-2xl border border-border shadow-card overflow-hidden flex flex-col",
                className
            )}
        >
            {/* Header */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between flex-shrink-0">
                <div>
                    <h2 className="text-[15px] font-semibold text-foreground">{title}</h2>
                    {subtitle && (
                        <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
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
