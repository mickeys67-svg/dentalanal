"use client";

import React from 'react';
import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend
} from 'recharts';

interface PerformanceChartProps {
    data: { name: string; 광고비: number; 전환수: number }[];
    height?: number;
}

export function PerformanceChart({ data, height = 300 }: PerformanceChartProps) {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                    data={data}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                    <defs>
                        <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#4F46E5" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorConversions" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                    <XAxis
                        dataKey="name"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: '#9CA3AF' }}
                        dy={10}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: '#9CA3AF' }}
                    />
                    <Tooltip
                        contentStyle={{
                            borderRadius: '8px',
                            border: 'none',
                            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Area
                        type="monotone"
                        dataKey="광고비"
                        stroke="#6366F1"
                        fillOpacity={1}
                        fill="url(#colorSpend)"
                        strokeWidth={4}
                        animationDuration={1500}
                    />
                    <Area
                        type="monotone"
                        dataKey="전환수"
                        stroke="#10B981"
                        fillOpacity={1}
                        fill="url(#colorConversions)"
                        strokeWidth={4}
                        animationDuration={2000}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
