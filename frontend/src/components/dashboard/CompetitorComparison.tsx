"use client";

import { CompetitorAnalysisResult } from "@/types";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UI_TEXT } from "@/lib/i18n";

interface CompetitorComparisonProps {
    data: CompetitorAnalysisResult | null;
    isLoading: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export function CompetitorComparison({ data, isLoading }: CompetitorComparisonProps) {
    if (isLoading) {
        return (
            <div className="w-full h-[400px] flex items-center justify-center border rounded-lg bg-gray-50/50">
                <div className="flex flex-col items-center gap-2">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <p className="text-sm text-muted-foreground">{UI_TEXT.COMPETITOR.LOADING}</p>
                </div>
            </div>
        );
    }

    if (!data || !data.competitors || data.competitors.length === 0) {
        return null; // Don't show if no data
    }

    const chartData = data.competitors.slice(0, 5).map(c => ({
        name: c.name,
        count: c.rank_count,
        avgRank: c.avg_rank.toFixed(1)
    }));

    return (
        <Card className="col-span-1 md:col-span-2">
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <span>{UI_TEXT.COMPETITOR.TITLE} (Top {data.top_n})</span>
                    <Badge variant="secondary">{data.keyword}</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Size 1: Chart */}
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={chartData}
                                layout="vertical"
                                margin={{
                                    top: 5,
                                    right: 30,
                                    left: 20,
                                    bottom: 5,
                                }}
                            >
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" hide />
                                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ borderRadius: '8px' }}
                                />
                                <Bar dataKey="count" name={UI_TEXT.COMPETITOR.CHART_LABEL} radius={[0, 4, 4, 0]} barSize={20}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Size 2: Table/List */}
                    <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                        <h4 className="text-sm font-semibold text-muted-foreground mb-2">{UI_TEXT.COMPETITOR.LIST_TITLE}</h4>
                        {data.competitors.map((comp, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border">
                                <div className="flex items-center gap-3">
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${idx < 3 ? "bg-primary" : "bg-gray-400"}`}>
                                        {idx + 1}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="font-medium text-sm truncate max-w-[120px]" title={comp.name}>{comp.name}</span>
                                    </div>
                                </div>
                                <div className="text-right text-xs text-muted-foreground">
                                    <div>{UI_TEXT.COMPETITOR.SHARE} <span className="text-foreground font-bold">{comp.share.toFixed(0)}%</span></div>
                                    <div>{UI_TEXT.COMPETITOR.AVG} <span className="text-foreground font-bold">{comp.avg_rank.toFixed(1)}{UI_TEXT.SUMMARY.UNIT_RANK}</span></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
