"use client";

import { useState } from "react";
import { ScoreCard } from "@/components/dashboard/ScoreCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { DashboardEmptyState } from "@/components/dashboard/DashboardEmptyState";
import { BarChart3, MousePointerClick, Wallet, Users, RefreshCw, Sparkles, ChevronRight, Loader2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDashboardSummary, getMetricsTrend, triggerSync, getAssistantQuickQueries, queryAssistant } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { format } from "date-fns";
import { toast } from "sonner";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

export default function DashboardPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [isSyncing, setIsSyncing] = useState(false);

    // 1. Fetch Summary KPIs
    const { data: summary, isLoading: isSummaryLoading } = useQuery({
        queryKey: ['dashboardSummary', selectedClient?.id],
        queryFn: () => getDashboardSummary(selectedClient?.id),
        enabled: !!selectedClient
    });

    // 2. Fetch Trend Data
    const { data: trend, isLoading: isTrendLoading } = useQuery({
        queryKey: ['metricsTrend', selectedClient?.id],
        queryFn: () => getMetricsTrend(selectedClient?.id),
        enabled: !!selectedClient
    });

    // 3. Manual Sync Mutation
    const syncMutation = useMutation({
        mutationFn: triggerSync,
        onMutate: () => setIsSyncing(true),
        onSuccess: () => {
            // In a real app, we might poll for status, but for now we just wait a bit and refetch
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
                queryClient.invalidateQueries({ queryKey: ['metricsTrend'] });
                setIsSyncing(false);
                toast.success("데이터 분석이 시작되었습니다. 잠시 후 새로고침 됩니다.");
            }, 3000);
        },
        onError: () => {
            setIsSyncing(false);
            toast.error("조사 시작에 실패했습니다.");
        }
    });

    const handleSync = () => {
        if (!confirm("실시간 조사를 시작하시겠습니까? (약 1-2분 소요)")) return;
        syncMutation.mutate();
    };

    // Derived States
    // Check if we have valid data (KPIs are non-zero or trend array has data)
    const hasData = summary && (summary.kpis?.some(k => Number(k.value) > 0) || (trend && trend.length > 0));

    // AI Quick Insight state
    const [aiResult, setAiResult] = useState<string | null>(null);
    const [activeQuickQuery, setActiveQuickQuery] = useState<string | null>(null);

    const { data: quickQueries = [] } = useQuery({
        queryKey: ['assistantQuickQueries'],
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
            toast.error('AI 분석 중 오류가 발생했습니다.');
        },
    });

    // Formatting helpers
    const formatCurrency = (val: number) => new Intl.NumberFormat('ko-KR').format(val);

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">대시보드</h1>
                    <p className="text-muted-foreground">
                        {selectedClient
                            ? `${selectedClient.name}의 마케팅 성과 현황입니다.`
                            : "프로젝트를 선택해주세요."}
                    </p>
                </div>
                {selectedClient && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleSync}
                            disabled={isSyncing}
                            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                            {isSyncing ? '조사 중...' : '데이터 업데이트'}
                        </button>
                    </div>
                )}
            </div>

            {!selectedClient || (!hasData && !isSummaryLoading) ? (
                <div className="mt-10">
                    <DashboardEmptyState onSync={handleSync} isSyncing={isSyncing} />
                </div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {summary?.kpis?.map((kpi, idx) => {
                            // Assign icons based on title keywords (simple heuristic)
                            let Icon = BarChart3;
                            if (kpi.title.includes("비용") || kpi.title.includes("광고비")) Icon = Wallet;
                            if (kpi.title.includes("노출")) Icon = Users;
                            if (kpi.title.includes("클릭")) Icon = MousePointerClick;

                            // Safe casting for value
                            const numValue = Number(kpi.value);

                            return (
                                <ScoreCard
                                    key={idx}
                                    title={kpi.title}
                                    value={formatCurrency(numValue)}
                                    prefix={kpi.prefix}
                                    suffix={kpi.suffix}
                                    change={kpi.change || 0}
                                    icon={Icon}
                                />
                            );
                        })}
                    </div>

                    {/* Charts Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
                        {/* Main Trend Chart (Left 4 cols) */}
                        <div className="lg:col-span-4 h-[400px]">
                            {trend && trend.length > 0 ? (
                                <PerformanceChart
                                    title="일별 성과 추이 (클릭/전환)"
                                    data={trend.map(t => ({
                                        date: format(new Date(t.date), 'MM/dd'),
                                        value: t.clicks // Default to clicks for main chart
                                    }))}
                                    color="#4F46E5"
                                />
                            ) : (
                                <div className="h-full rounded-xl border bg-card flex items-center justify-center text-muted-foreground">
                                    데이터 없음
                                </div>
                            )}
                        </div>

                        {/* Secondary Chart (Right 3 cols) */}
                        <div className="lg:col-span-3 h-[400px]">
                            {trend && trend.length > 0 ? (
                                <PerformanceChart
                                    title="일별 전환 추이"
                                    data={trend.map(t => ({
                                        date: format(new Date(t.date), 'MM/dd'),
                                        value: t.conversions
                                    }))}
                                    color="#10B981"
                                />
                            ) : (
                                <div className="h-full rounded-xl border bg-card flex items-center justify-center text-muted-foreground">
                                    데이터 없음
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Adriel-style Grid Placeholders (To be implemented in Phase 2) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 h-[200px] flex items-center justify-center text-muted-foreground border-dashed bg-gray-50/50">
                            <div>
                                <p className="font-medium text-center mb-1">+ 채널별 점유율 (SOV)</p>
                                <p className="text-xs text-gray-400 text-center">네이버 vs 인스타 vs 블로그 비율 분석</p>
                            </div>
                        </div>
                        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 h-[200px] flex items-center justify-center text-muted-foreground border-dashed bg-gray-50/50">
                            <div>
                                <p className="font-medium text-center mb-1">+ 키워드 랭킹 요약</p>
                                <p className="text-xs text-gray-400 text-center">주요 키워드(임플란트 등) 순위 변동</p>
                            </div>
                        </div>
                    </div>

                    {/* AI 인사이트 패널 */}
                    <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/60 to-white shadow-sm p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <div className="p-1.5 bg-indigo-600 rounded-lg">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                                <h3 className="text-sm font-bold text-gray-900">AI 빠른 인사이트</h3>
                            </div>
                            <Link
                                href="/assistant"
                                className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-semibold"
                            >
                                전체 AI 어시스턴트 <ChevronRight className="w-3 h-3" />
                            </Link>
                        </div>

                        {/* 빠른 질문 버튼 */}
                        <div className="flex gap-2 flex-wrap mb-4">
                            {quickQueries.slice(0, 4).map((q) => (
                                <button
                                    key={q.id}
                                    onClick={() => {
                                        setAiResult(null);
                                        aiMutation.mutate({ query: q.id });
                                    }}
                                    disabled={aiMutation.isPending}
                                    className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors disabled:opacity-40 ${
                                        activeQuickQuery === q.id && aiResult
                                            ? 'bg-indigo-600 text-white border-indigo-600'
                                            : 'bg-white text-indigo-700 border-indigo-200 hover:bg-indigo-50'
                                    }`}
                                >
                                    {q.label}
                                </button>
                            ))}
                        </div>

                        {/* 결과 영역 */}
                        <div className="min-h-[80px] bg-white/70 rounded-xl border border-indigo-50 p-4">
                            {aiMutation.isPending ? (
                                <div className="flex items-center gap-2 text-indigo-400 text-sm">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    AI가 분석 중입니다...
                                </div>
                            ) : aiResult ? (
                                <div className="prose prose-sm max-w-none prose-p:text-gray-700 prose-strong:text-gray-900 prose-headings:text-gray-900">
                                    <ReactMarkdown>{aiResult}</ReactMarkdown>
                                </div>
                            ) : (
                                <p className="text-gray-400 text-xs">위 버튼을 클릭하면 AI 인사이트를 바로 확인할 수 있습니다.</p>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
