"use client";

import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

type AccentColor = "indigo" | "emerald" | "amber" | "rose" | "violet";

interface ScoreCardProps {
    title: string;
    value: string;
    change: number;
    prefix?: string;
    suffix?: string;
    description?: string;
    icon?: React.ComponentType<{ className?: string }>;
    accentColor?: AccentColor;
}

const accentStyles: Record<AccentColor, { bar: string; iconBg: string; iconColor: string }> = {
    indigo: {
        bar: "bg-indigo-500",
        iconBg: "bg-indigo-50",
        iconColor: "text-indigo-600",
    },
    emerald: {
        bar: "bg-emerald-500",
        iconBg: "bg-emerald-50",
        iconColor: "text-emerald-600",
    },
    amber: {
        bar: "bg-amber-500",
        iconBg: "bg-amber-50",
        iconColor: "text-amber-600",
    },
    rose: {
        bar: "bg-rose-500",
        iconBg: "bg-rose-50",
        iconColor: "text-rose-600",
    },
    violet: {
        bar: "bg-violet-500",
        iconBg: "bg-violet-50",
        iconColor: "text-violet-600",
    },
};

export function ScoreCard({
    title,
    value,
    change,
    prefix,
    suffix,
    icon: Icon,
    accentColor = "indigo",
}: ScoreCardProps) {
    const isPositive = change >= 0;
    const styles = accentStyles[accentColor];

    return (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden hover:shadow-card-hover transition-shadow duration-200">
            {/* Top accent bar */}
            <div className={cn("h-1", styles.bar)} />

            <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                    <span className="text-sm font-medium text-slate-500 leading-tight">{title}</span>
                    {Icon && (
                        <div className={cn("p-2 rounded-lg flex-shrink-0", styles.iconBg)}>
                            <Icon className={cn("h-4 w-4", styles.iconColor)} />
                        </div>
                    )}
                </div>

                <div>
                    <span className="text-2xl font-bold text-slate-900 tracking-tight">
                        {prefix}
                        {value}
                        {suffix}
                    </span>
                </div>

                <div className="flex items-center mt-3 gap-2">
                    <span
                        className={cn(
                            "inline-flex items-center gap-0.5 text-xs font-semibold rounded-full px-2 py-0.5",
                            isPositive
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-red-50 text-red-600"
                        )}
                    >
                        {isPositive ? (
                            <ArrowUpRight className="h-3 w-3" />
                        ) : (
                            <ArrowDownRight className="h-3 w-3" />
                        )}
                        {Math.abs(change)}%
                    </span>
                    <span className="text-xs text-slate-400">지난달 대비</span>
                </div>
            </div>
        </div>
    );
}
