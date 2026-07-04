"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { BrainCircuit, Loader2, Info } from "lucide-react";
import { UI_TEXT } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";

interface SentimentItem {
    name: string;
    value: number;
    color: string;
}

interface SentimentGaugeProps {
    isLoading: boolean;
    // 실데이터가 연동되면 [{name,value,color}] 형태로 주입. 없으면 미연동 상태 표시.
    data?: SentimentItem[];
}

// ⚠️ 가짜 데이터 금지:
//   이전엔 항상 긍정65/중립25/부정10 하드코딩 파이를 "AI 감성분석"으로 표시했다(사기).
//   실제 감성 분석은 실제 언급 텍스트 + 감성 분류 모델 연동이 필요하다.
//   진짜 데이터(data prop)가 없으면 가짜 파이를 그리지 않고 미연동 상태를 정직하게 표시한다.
export function SentimentGauge({ isLoading, data }: SentimentGaugeProps) {
    const hasRealData = Array.isArray(data) && data.length > 0;

    if (isLoading) {
        return (
            <Card className="h-[400px] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </Card>
        );
    }

    const total = hasRealData ? data!.reduce((s, d) => s + (d.value || 0), 0) : 0;
    const positive = hasRealData ? data!.find((d) => d.name === UI_TEXT.VIRAL.POSITIVE) : undefined;
    const positivePct = positive && total > 0 ? Math.round((positive.value / total) * 100) : null;

    return (
        <Card className="h-[400px] flex flex-col">
            <CardHeader>
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <BrainCircuit className="w-5 h-5 text-purple-500" />
                    {UI_TEXT.VIRAL.SENTIMENT_TITLE}
                    <Badge variant="secondary" className="bg-slate-100 text-slate-500 ml-auto text-[10px]">
                        {hasRealData ? "AI" : "미연동"}
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 min-h-0">
                {!hasRealData ? (
                    // 정직한 미연동 상태 — 가짜 수치 없음
                    <div className="h-full w-full flex flex-col items-center justify-center text-center px-6">
                        <Info className="w-8 h-8 text-slate-300 mb-3" />
                        <p className="text-sm font-medium text-slate-500">감성 분석 미연동</p>
                        <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                            실제 언급 텍스트 기반 감성 분류가 아직 연동되지 않았습니다.
                            <br />연동 전까지는 수치를 표시하지 않습니다.
                        </p>
                    </div>
                ) : (
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
                                    {data!.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Legend
                                    verticalAlign="bottom"
                                    height={36}
                                    formatter={(value) => (
                                        <span className="text-sm font-medium text-slate-600 ml-1">{value}</span>
                                    )}
                                />
                            </PieChart>
                        </ResponsiveContainer>

                        {positivePct !== null && (
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-[60%] text-center pointer-events-none">
                                <div className="text-2xl font-bold text-gray-900">{positivePct}%</div>
                                <div className="text-xs text-muted-foreground">{UI_TEXT.VIRAL.POSITIVE}</div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
