"use client";

import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface ScoreCardProps {
    title: string;
    value: string;
    change: number; // percentage
    prefix?: string;
    suffix?: string;
    description?: string;
    icon?: React.ComponentType<{ className?: string }>;
}

export function ScoreCard({ title, value, change, prefix, suffix, icon: Icon }: ScoreCardProps) {
    const isPositive = change >= 0;

    return (
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm">
            <div className="p-6 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">{title}</span>
                    {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
                </div>

                <div className="flex items-baseline gap-2 mt-2">
                    <span className="text-2xl font-bold tracking-tight">
                        {prefix}{value}{suffix}
                    </span>
                </div>

                <div className="flex items-center mt-1 text-xs">
                    <span
                        className={cn(
                            "flex items-center font-medium",
                            isPositive ? "text-green-600" : "text-red-600"
                        )}
                    >
                        {isPositive ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                        {Math.abs(change)}%
                    </span>
                    <span className="text-muted-foreground ml-2">지난달 대비</span>
                </div>
            </div>
        </div>
    );
}
