"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { BrainCircuit, Loader2 } from "lucide-react";
import { UI_TEXT } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";

interface SentimentGaugeProps {
    isLoading: boolean;
    data?: any; // To be typed properly when API is ready
}

export function SentimentGauge({ isLoading }: SentimentGaugeProps) {
    // Mock Data for Demo
    const data = [
        { name: UI_TEXT.VIRAL.POSITIVE, value: 65, color: '#22c55e' }, // Green
        { name: UI_TEXT.VIRAL.NEUTRAL, value: 25, color: '#94a3b8' },  // Gray
        { name: UI_TEXT.VIRAL.NEGATIVE, value: 10, color: '#ef4444' },  // Red
    ];

    if (isLoading) {
        return (
            <Card className="h-[400px] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </Card>
        );
    }

    return (
        <Card className="h-[400px] flex flex-col">
            <CardHeader>
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <BrainCircuit className="w-5 h-5 text-purple-500" />
                    {UI_TEXT.VIRAL.SENTIMENT_TITLE}
                    <Badge variant="secondary" className="bg-purple-100 text-purple-700 ml-auto text-[10px]">
                        AI Beta
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 min-h-0">
                <div className="h-full w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            />
                            <Legend
                                verticalAlign="bottom"
                                height={36}
                                formatter={(value, entry: any) => (
                                    <span className="text-sm font-medium text-slate-600 ml-1">{value}</span>
                                )}
                            />
                        </PieChart>
                    </ResponsiveContainer>

                    {/* Center Text */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-[60%] text-center pointer-events-none">
                        <div className="text-2xl font-bold text-gray-900">65%</div>
                        <div className="text-xs text-muted-foreground">{UI_TEXT.VIRAL.POSITIVE}</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
