import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';

interface KPICardProps {
    title: string;
    value: string | number;
    change: number;
    prefix?: string;
    suffix?: string;
    precision?: number;
}

export function KPICard({
    title,
    value,
    change,
    prefix = '',
    suffix = '',
    precision = 1
}: KPICardProps) {
    const isPositive = change >= 0;

    return (
        <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-500">{title}</h3>
                <div className={clsx(
                    "flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
                    isPositive ? "bg-green-50 text-success" : "bg-red-50 text-danger"
                )}>
                    {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(change).toFixed(precision)}%
                </div>
            </div>
            <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-bold tracking-tight text-gray-900 font-mono">
                    {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
                </span>
            </div>
            <div className="mt-1 text-xs text-gray-400">vs 지난달</div>
        </div>
    );
}
