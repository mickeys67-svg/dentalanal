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
        <div className="bg-card rounded-2xl border border-border shadow-card p-5 transition-shadow hover:shadow-card-hover animate-kl-fade">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
                <div
                    className={cn(
                        "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold",
                        isPositive ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
                    )}
                >
                    {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(change).toFixed(precision)}%
                </div>
            </div>
            <div className="flex items-baseline gap-1">
                <span className="font-display text-[26px] font-semibold tracking-tight text-foreground tabular-nums">
                    {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
                </span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground/70">vs 지난달</div>
        </div>
    );
}
