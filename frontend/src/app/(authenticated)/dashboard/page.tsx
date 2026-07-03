"use client";

import { useState } from "react";
import { ScoreCard } from "@/components/dashboard/ScoreCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { DashboardEmptyState } from "@/components/dashboard/DashboardEmptyState";
import {
    BarChart3,
    MousePointerClick,
    Wallet,
    Users,
    RefreshCw,
    Sparkles,
    ChevronRight,
    Loader2,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    getDashboardSummary,
    getMetricsTrend,
    triggerSync,
    getAssistantQuickQueries,
    queryAssistant,
} from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { format } from "date-fns";
import { toast } from "sonner";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

type AccentColor = "indigo" | "emerald" | "amber" | "rose" | "violet";

const KPI_ACCENT_COLORS: AccentColor[] = ["indigo", "emerald", "amber", "rose"];

function getKPIIcon(title: string) {
    if (title.includes("비용") || title.includes("광고비")) return Wallet;
    if (title.includes("노출")) return Users;
    if (title.includes("클릭")) return MousePointerClick;
    return BarChart3;
}

export default function DashboardPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [isSyncing, setIsSyncing] = useState(false);
    const [aiResult, setAiResult] = useState<string | null>(null);
    const [activeQuickQuery, setActiveQuickQuery] = useState<string | null>(null);

    const { data: summary, isLoading: isSummaryLoading } = useQuery({
        queryKey: ["dashboardSummary", selectedClient?.id],
        queryFn: () => getDashboardSummary(selectedClient?.id),
        enabled: !!selectedClient,
    });

    const { data: trend } = useQuery({
        queryKey: ["metricsTrend", selectedClient?.id],
        queryFn: () => getMetricsTrend(selectedClient?.id),
        enabled: !!selectedClient,
    });

    const syncMutation = useMutation({
        mutationFn: triggerSync,
        onMutate: () => setIsSyncing(true),
        onSuccess: () => {
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
                queryClient.invalidateQueries({ queryKey: ["metricsTrend"] });
                setIsSyncing(false);
                toast.success("데이터 분석이 완료되었습니다.");
            }, 3000);
        },
        onError: () => {
            setIsSyncing(false);
            toast.error("조사 시작에 실패했습니다.");
        },
    });

    const handleSync = () => {
        if (!confirm("실시간 조사를 시작하시겠습니까? (약 1-2분 소요)")) return;
        syncMutation.mutate();
    };

    const { data: quickQueries = [] } = useQuery({
        queryKey: ["assistantQuickQueries"],
        queryFn: getAssistantQuickQueries,
        enabled: !!selectedClient,
    });

    const aiMutation = useMutation({
        mutationFn: ({ query }: { query: string }) =>
            queryAssistant(query, selectedClient?.id),
        onSuccess: (data, variables) => {
            setAiResult(data.report);
            setActiveQuickQuery(variables.query);
        },
        onError: () => {
            toast.error("AI 분석 중 오류가 발생했습니다.");
        },
    });

    const hasData =
        summary &&
        (summary.kpis?.some((k: any) => Number(k.value) > 0) ||
            (trend && trend.length > 0));

    const formatCurrency = (val: number) =>
        new Intl.NumberFormat("ko-KR").format(val);

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 tracking-tight">대시보드</h1>
                    <p className="text-sm text-slate-500 mt-0.5">
                        {selectedClient
                            ? `${selectedClient.name}의 마케팅 성과 현황`
                            : "분석할 프로젝트를 선택해주세요."}
                    </p>
                </div>
                {selectedClient && (
                    <button
                        onClick={handleSync}
                        disabled={isSyncing}
                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium
                                   bg-white border border-slate-200 text-slate-700
                                   hover:bg-slate-50 hover:border-slate-300
                                   rounded-xl transition-colors shadow-card
                                   disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                        {isSyncing ? "조사 중..." : "데이터 업데이트"}
                    </button>
                )}
            </div>

            {!selectedClient || (!hasData && !isSummaryLoading) ? (
                <DashboardEmptyState onSync={handleSync} isSyncing={isSyncing} />
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {summary?.kpis?.map((kpi: any, idx: number) => (
                            <ScoreCard
                                key={idx}
                                title={kpi.title}
                                value={formatCurrency(Number(kpi.value))}
                                prefix={kpi.prefix}
                                suffix={kpi.suffix}
                                change={kpi.change || 0}
                                icon={getKPIIcon(kpi.title)}
                                accentColor={KPI_ACCENT_COLORS[idx % KPI_ACCENT_COLORS.length]}
                            />
                        ))}
                    </div>

                    {/* Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-7 gap-5">
                        <div className="lg:col-span-4 h-[360px]">
                            {trend && trend.length > 0 ? (
                                <PerformanceChart
                                    title="일별 클릭 추이"
                                    data={trend.map((t: any) => ({
                                        date: format(new Date(t.date), "MM/dd"),
                                        value: t.clicks,
                                    }))}
                                    color="#4F46E5"
                                />
                            ) : (
                                <div className="h-full rounded-2xl border border-slate-100 bg-white flex items-center justify-center text-slate-400 text-sm shadow-card">
                                    데이터 없음
                                </div>
                            )}
                        </div>
                        <div className="lg:col-span-3 h-[360px]">
                            {trend && trend.length > 0 ? (
                                <PerformanceChart
                                    title="일별 전환 추이"
                                    data={trend.map((t: any) => ({
                                        date: format(new Date(t.date), "MM/dd"),
                                        value: t.conversions,
                                    }))}
                                    color="#10B981"
                                />
                            ) : (
                                <div className="h-full rounded-2xl border border-slate-100 bg-white flex items-center justify-center text-slate-400 text-sm shadow-card">
                                    데이터 없음
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Placeholder Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {[
                            { title: "채널별 점유율 (SOV)", desc: "네이버 vs 인스타 vs 블로그 비율 분석" },
                            { title: "키워드 랭킹 요약", desc: "주요 키워드(임플란트 등) 순위 변동" },
                        ].map((item) => (
                            <div
                                key={item.title}
                                className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-6 h-[180px] flex items-center justify-center"
                            >
                                <div className="text-center">
                                    <p className="text-sm font-semibold text-slate-500 mb-1">+ {item.title}</p>
                                    <p className="text-xs text-slate-400">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* AI Quick Insight Panel */}
                    <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/70 to-white shadow-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2.5">
                                <div className="p-1.5 bg-indigo-600 rounded-lg shadow-sm shadow-indigo-200">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-900">AI 빠른 인사이트</h3>
                                    <p className="text-xs text-slate-400">Gemini AI 기반 마케팅 분석</p>
                                </div>
                            </div>
                            <Link
                                href="/assistant"
                                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
                            >
                                전체 어시스턴트
                                <ChevronRight className="w-3.5 h-3.5" />
                            </Link>
                        </div>

                        {/* Quick query buttons */}
                        <div className="flex gap-2 flex-wrap mb-4">
                            {quickQueries.slice(0, 4).map((q: any) => (
                                <button
                                    key={q.id}
                                    onClick={() => {
                                        setAiResult(null);
                                        aiMutation.mutate({ query: q.id });
                                    }}
                                    disabled={aiMutation.isPending}
                                    className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-all duration-150
                                                disabled:opacity-40 ${
                                        activeQuickQuery === q.id && aiResult
                                            ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                                            : "bg-white text-indigo-700 border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50"
                                    }`}
                                >
                                    {q.label}
                                </button>
                            ))}
                        </div>

                        {/* Result area */}
                        <div className="min-h-[80px] bg-white/80 rounded-xl border border-indigo-100/60 p-4">
                            {aiMutation.isPending ? (
                                <div className="flex items-center gap-2 text-indigo-500 text-sm">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    AI가 분석 중입니다...
                                </div>
                            ) : aiResult ? (
                                <div className="prose prose-sm max-w-none prose-p:text-slate-700 prose-strong:text-slate-900 prose-headings:text-slate-900">
                                    <ReactMarkdown>{aiResult}</ReactMarkdown>
                                </div>
                            ) : (
                                <p className="text-slate-400 text-xs">
                                    위 버튼을 클릭하면 AI 인사이트를 바로 확인할 수 있습니다.
                                </p>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
