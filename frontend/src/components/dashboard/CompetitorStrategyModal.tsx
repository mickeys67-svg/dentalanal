"use client";

import { useMutation } from "@tanstack/react-query";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    TrendingUp,
    TrendingDown,
    Minus,
    BarChart2,
    Clock,
    Calendar,
    Tag,
} from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    Cell,
} from "recharts";
import {
    analyzeCompetitorStrategy,
    CompetitorStrategyAnalysis,
} from "@/lib/api";

interface CompetitorStrategyModalProps {
    open: boolean;
    onClose: () => void;
    targetId: string;
    targetName: string;
    platform: "NAVER_PLACE" | "NAVER_VIEW";
}

const DOW_ORDER = ["월", "화", "수", "목", "금", "토", "일"];

function TrendDirectionBadge({ direction }: { direction: string }) {
    if (direction === "상승")
        return (
            <Badge className="bg-green-100 text-green-700 border-green-300">
                <TrendingUp className="w-3 h-3 mr-1" /> 상승 추세
            </Badge>
        );
    if (direction === "하락")
        return (
            <Badge className="bg-red-100 text-red-700 border-red-300">
                <TrendingDown className="w-3 h-3 mr-1" /> 하락 추세
            </Badge>
        );
    return (
        <Badge className="bg-gray-100 text-gray-600 border-gray-300">
            <Minus className="w-3 h-3 mr-1" /> 보합
        </Badge>
    );
}

function AnalysisContent({ data }: { data: CompetitorStrategyAnalysis }) {
    // 시간대별 데이터 변환 (0~23시)
    const hourData = Array.from({ length: 24 }, (_, i) => ({
        hour: `${i}시`,
        count: data.activity_by_hour[String(i)] ?? 0,
    }));

    // 요일별 데이터 (월~일 순서 정렬)
    const dowData = DOW_ORDER.map((day) => ({
        day,
        count: data.activity_by_dow[day] ?? 0,
    }));

    const maxHour = Math.max(...hourData.map((d) => d.count), 1);
    const maxDow = Math.max(...dowData.map((d) => d.count), 1);

    return (
        <div className="space-y-6">
            {/* 분석 헤더 */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="text-sm text-muted-foreground">
                    분석 기간: {data.analysis_period}
                </div>
                <TrendDirectionBadge direction={data.trend_direction} />
            </div>

            {/* 순위 트렌드 */}
            {data.rank_trend.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <BarChart2 className="w-4 h-4 text-blue-500" />
                        순위 트렌드
                    </h3>
                    <div className="h-[160px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={data.rank_trend}
                                margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 10 }}
                                    tickFormatter={(v: string) => v.slice(5)}
                                />
                                <YAxis
                                    reversed
                                    domain={[1, "auto"]}
                                    tick={{ fontSize: 10 }}
                                    tickFormatter={(v: number) => `${v}위`}
                                />
                                <Tooltip
                                    contentStyle={{ borderRadius: "6px", fontSize: "11px" }}
                                    formatter={(v: number | undefined) =>
                                        v !== undefined ? [`${v}위`, "평균 순위"] : ["-", "평균 순위"]
                                    }
                                    labelFormatter={(l) => `날짜: ${l}`}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="avg_rank"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={{ r: 2 }}
                                    activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* 주력 키워드 */}
            {data.top_keywords.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Tag className="w-4 h-4 text-purple-500" />
                        주력 키워드 TOP {data.top_keywords.length}
                    </h3>
                    <div className="space-y-2">
                        {data.top_keywords.slice(0, 8).map((kw, idx) => (
                            <div
                                key={kw.term}
                                className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border text-sm"
                            >
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0 ${
                                            idx < 3 ? "bg-purple-500" : "bg-gray-400"
                                        }`}
                                    >
                                        {idx + 1}
                                    </span>
                                    <span className="font-medium">{kw.term}</span>
                                </div>
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span>평균 {kw.avg_rank.toFixed(1)}위</span>
                                    <span>최고 {kw.best_rank}위</span>
                                    <span>{kw.appearances}회 노출</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 시간대별 / 요일별 활동 패턴 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* 시간대별 */}
                <div>
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-orange-500" />
                        시간대별 활동
                    </h3>
                    <div className="h-[120px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={hourData}
                                margin={{ top: 4, right: 4, left: -20, bottom: 4 }}
                            >
                                <XAxis
                                    dataKey="hour"
                                    tick={{ fontSize: 9 }}
                                    interval={2}
                                    tickFormatter={(v: string) => v.replace("시", "")}
                                />
                                <YAxis tick={{ fontSize: 9 }} />
                                <Tooltip
                                    contentStyle={{ fontSize: "10px" }}
                                    formatter={(v: number | undefined) => [v ?? 0, "활동 수"]}
                                />
                                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                                    {hourData.map((entry, i) => (
                                        <Cell
                                            key={i}
                                            fill={
                                                entry.count === maxHour
                                                    ? "#f97316"
                                                    : "#e2e8f0"
                                            }
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 요일별 */}
                <div>
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-green-500" />
                        요일별 활동
                    </h3>
                    <div className="h-[120px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={dowData}
                                margin={{ top: 4, right: 4, left: -20, bottom: 4 }}
                            >
                                <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                                <YAxis tick={{ fontSize: 9 }} />
                                <Tooltip
                                    contentStyle={{ fontSize: "10px" }}
                                    formatter={(v: number | undefined) => [v ?? 0, "활동 수"]}
                                />
                                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                                    {dowData.map((entry, i) => (
                                        <Cell
                                            key={i}
                                            fill={
                                                entry.count === maxDow
                                                    ? "#22c55e"
                                                    : "#e2e8f0"
                                            }
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}

export function CompetitorStrategyModal({
    open,
    onClose,
    targetId,
    targetName,
    platform,
}: CompetitorStrategyModalProps) {
    const { data, isPending, error, mutate } = useMutation({
        mutationFn: () =>
            analyzeCompetitorStrategy({
                target_id: targetId,
                platform,
                days: 30,
            }),
    });

    // 모달 열릴 때 자동 분석 시작
    const handleOpenChange = (isOpen: boolean) => {
        if (isOpen && !data && !isPending) {
            mutate();
        }
        if (!isOpen) onClose();
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-base">
                        <BarChart2 className="w-5 h-5 text-blue-500" />
                        {targetName} — 전략 분석
                    </DialogTitle>
                </DialogHeader>

                {isPending && (
                    <div className="space-y-4 py-2">
                        {[160, 120, 100].map((h, i) => (
                            <Skeleton key={i} style={{ height: h }} className="w-full rounded-lg" />
                        ))}
                    </div>
                )}

                {error && !isPending && (
                    <div className="py-8 text-center text-sm text-muted-foreground">
                        분석 데이터를 불러오지 못했습니다.
                        <br />
                        데이터가 충분히 쌓이면 자동으로 표시됩니다.
                    </div>
                )}

                {data?.analysis && !isPending && (
                    <AnalysisContent data={data.analysis} />
                )}
            </DialogContent>
        </Dialog>
    );
}
