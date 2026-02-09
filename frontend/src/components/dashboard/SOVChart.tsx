'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SOVData {
    keyword: string;
    total_items: number;
    target_hits: number;
    sov_score: number;
}

interface SOVChartProps {
    data: SOVData[];
}

export function SOVChart({ data }: SOVChartProps) {
    return (
        <div className="bg-white p-6 rounded-lg shadow h-[400px]">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Share of Voice (SOV)</h3>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="keyword" />
                    <YAxis unit="%" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="sov_score" name="SOV %" fill="#8884d8" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
