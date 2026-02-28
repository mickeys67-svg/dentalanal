"use client";

import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area,
} from "recharts";

interface DataPoint {
    date: string;
    value: number;
}

interface PerformanceChartProps {
    data: DataPoint[];
    title: string;
    color?: string;
}

export function PerformanceChart({
    data,
    title,
    color = "#4F46E5",
}: PerformanceChartProps) {
    return (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-card h-full flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-50 flex-shrink-0">
                <h3 className="text-[15px] font-semibold text-slate-900">{title}</h3>
                <p className="text-xs text-slate-400 mt-0.5">최근 30일 성과 그래프</p>
            </div>
            <div className="flex-1 p-4 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={data}
                        margin={{ top: 8, right: 8, left: -24, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            vertical={false}
                            stroke="#F1F5F9"
                        />
                        <XAxis
                            dataKey="date"
                            stroke="#94A3B8"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                        />
                        <YAxis
                            stroke="#94A3B8"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(v) => `${v}`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#ffffff",
                                borderColor: "#E2E8F0",
                                borderRadius: "10px",
                                fontSize: "12px",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                            }}
                            cursor={{
                                stroke: "#94A3B8",
                                strokeWidth: 1,
                                strokeDasharray: "4 4",
                            }}
                        />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={color}
                            strokeWidth={2}
                            fillOpacity={1}
                            fill={`url(#grad-${title})`}
                            dot={false}
                            activeDot={{
                                r: 5,
                                fill: color,
                                stroke: "#ffffff",
                                strokeWidth: 2,
                            }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
