'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface CompetitorData {
    name: string;
    rank_count: number;
    avg_rank: number;
    share: number;
}

interface MarketShareChartProps {
    data: CompetitorData[];
    title: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

export function MarketShareChart({ data, title }: MarketShareChartProps) {
    const chartData = (data || []).slice(0, 10).map(item => ({
        name: item.name,
        value: parseFloat((item.share || 0).toFixed(1))
    }));

    if (chartData.length === 0) {
        return (
            <div className="bg-white p-6 rounded-lg shadow h-[400px] flex items-center justify-center">
                <p className="text-gray-500">점유율 데이터가 없습니다.</p>
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-lg shadow h-[400px]">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="45%"
                        labelLine={false}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    >
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                    <Legend layout="horizontal" verticalAlign="bottom" align="center" />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
