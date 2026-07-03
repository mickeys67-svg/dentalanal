import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
    title: string;
    value: string | number;
    change: number;
    prefix?: string;
    suffix?: string;
    precision?: number;
}

export function KPICard({ title, value, change, prefix = '', suffix = '', precision = 1 }: KPICardProps) {
    const isPositive = change >= 0;

    return (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-card p-5 transition-shadow hover:shadow-card-hover">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-slate-500">{title}</h3>
                <div
                    className={cn(
                        "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold",
                        isPositive ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-600"
                    )}
                >
                    {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(change).toFixed(precision)}%
                </div>
            </div>
            <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold tracking-tight text-slate-900 tabular-nums">
                    {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
                </span>
            </div>
            <div className="mt-1 text-xs text-slate-400">vs 지난달</div>
        </div>
    );
}
