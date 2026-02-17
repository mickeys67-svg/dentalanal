"use client";

import { useState } from "react";
import { ScoreCard } from "@/components/dashboard/ScoreCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { DashboardEmptyState } from "@/components/dashboard/DashboardEmptyState";
import { BarChart3, MousePointerClick, Wallet, Users, RefreshCw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDashboardSummary, getMetricsTrend, triggerSync } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { format } from "date-fns";

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
                alert("데이터 분석이 시작되었습니다. 잠시 후 새로고침 됩니다.");
            }, 3000);
        },
        onError: () => {
            setIsSyncing(false);
            alert("조사 시작에 실패했습니다.");
        }
    });

    const handleSync = () => {
        if (!confirm("실시간 조사를 시작하시겠습니까? (약 1-2분 소요)")) return;
        syncMutation.mutate();
    };

    // Derived States
    // Check if we have valid data (KPIs are non-zero or trend array has data)
    const hasData = summary && (summary.kpis?.some(k => Number(k.value) > 0) || (trend && trend.length > 0));

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
                </>
            )}
        </div>
    );
}
