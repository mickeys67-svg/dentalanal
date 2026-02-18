"use client";

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRoasTracking, getInefficientAds, getBudgetReallocation } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, LineChart, Line,
} from 'recharts';
import {
    TrendingUp, TrendingDown, AlertTriangle, DollarSign,
    Target, Zap, Loader2, ArrowUpRight, ArrowDownRight, Minus,
} from 'lucide-react';
import clsx from 'clsx';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

export default function AdsPage() {
    const { selectedClient } = useClient();
    const [days, setDays] = useState(30);

    const { data: roasData, isLoading: roasLoading } = useQuery({
        queryKey: ['roas-tracking', selectedClient?.id, days],
        queryFn: () => getRoasTracking(selectedClient!.id, days),
        enabled: !!selectedClient,
    });

    const { data: inefficientData, isLoading: inefficientLoading } = useQuery({
        queryKey: ['inefficient-ads', selectedClient?.id, days],
        queryFn: () => getInefficientAds(selectedClient!.id, days),
        enabled: !!selectedClient,
    });

    const { data: budgetData, isLoading: budgetLoading } = useQuery({
        queryKey: ['budget-reallocation', selectedClient?.id, days],
        queryFn: () => getBudgetReallocation(selectedClient!.id, days),
        enabled: !!selectedClient,
    });

    if (!selectedClient) {
        return (
            <EmptyClientPlaceholder
                title="분석할 업체를 선택해주세요"
                description="업체를 선택하면 광고 성과 분석 및 ROI 최적화 데이터를 확인할 수 있습니다."
            />
        );
    }

    const isLoading = roasLoading || inefficientLoading || budgetLoading;
    const campaigns: any[]   = roasData?.data?.campaigns ?? [];
    const summary: any        = roasData?.data?.summary ?? {};
    const inefficientAds: any[] = inefficientData?.inefficient_ads ?? [];
    const budgetRecs: any[]   = budgetData?.data?.recommendations ?? [];
    const budgetSummary: any  = budgetData?.data ?? {};

    return (
        <div className="p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* 헤더 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        광고 성과 대시보드 <Zap className="w-5 h-5 text-amber-400 fill-amber-400" />
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        {roasData?.data?.period ?? '광고 성과 데이터 분석 중...'}
                    </p>
                </div>
                <div className="flex bg-gray-100 p-1 rounded-xl">
                    {[7, 30, 90].map((d) => (
                        <button
                            key={d}
                            onClick={() => setDays(d)}
                            className={clsx(
                                "px-4 py-1.5 text-xs font-bold rounded-lg transition-all",
                                days === d
                                    ? "bg-white text-indigo-600 shadow-sm"
                                    : "text-gray-400 hover:text-gray-600"
                            )}
                        >
                            {d === 7 ? '7일' : d === 30 ? '30일' : '90일'}
                        </button>
                    ))}
                </div>
            </div>

            {isLoading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                </div>
            ) : (
                <>
                    {/* KPI 카드 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <AdsKpiCard
                            label="전체 캠페인"
                            value={`${summary.total_campaigns ?? campaigns.length}개`}
                            icon={Target}
                            color="indigo"
                        />
                        <AdsKpiCard
                            label="평균 ROAS"
                            value={`${summary.avg_roas ?? 0}%`}
                            icon={TrendingUp}
                            color="green"
                        />
                        <AdsKpiCard
                            label="비효율 광고"
                            value={`${inefficientData?.count ?? 0}개`}
                            icon={AlertTriangle}
                            color={inefficientData?.count > 0 ? 'amber' : 'green'}
                        />
                        <AdsKpiCard
                            label="예산 절감 가능"
                            value={
                                budgetSummary.net_change
                                    ? `₩${Math.abs(budgetSummary.net_change).toLocaleString()}`
                                    : '-'
                            }
                            icon={DollarSign}
                            color="blue"
                        />
                    </div>

                    {/* ROAS 차트 */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <ErrorBoundary name="캠페인별 ROAS 차트">
                        <DashboardWidget title="캠페인별 ROAS" subtitle="캠페인별 광고비 대비 수익률(ROAS) 비교">
                            {campaigns.length > 0 ? (
                                <div className="h-72 mt-4">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={campaigns} margin={{ top: 4, right: 16, left: 0, bottom: 40 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                                            <XAxis
                                                dataKey="campaign_name"
                                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                                axisLine={false}
                                                tickLine={false}
                                                interval={0}
                                                angle={-20}
                                                textAnchor="end"
                                            />
                                            <YAxis
                                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                                axisLine={false}
                                                tickLine={false}
                                                unit="%"
                                            />
                                            <Tooltip
                                                formatter={(v: number | string | undefined) => [`${v ?? 0}%`, 'ROAS']}
                                                contentStyle={{ borderRadius: 12, border: '1px solid #F3F4F6', fontSize: 12 }}
                                            />
                                            <Bar dataKey="roas" fill="#6366F1" radius={[6, 6, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <NoDataPlaceholder />
                            )}
                        </DashboardWidget>
                        </ErrorBoundary>

                        <ErrorBoundary name="ROAS 추이 차트">
                        <DashboardWidget
                            title="ROAS 추이"
                            subtitle={`${summary.best_performer ?? '최고 성과'} 캠페인 일별 ROAS 변화`}
                        >
                            {campaigns[0]?.trend?.length > 0 ? (
                                <div className="h-72 mt-4">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={campaigns[0].trend} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                                axisLine={false}
                                                tickLine={false}
                                            />
                                            <YAxis
                                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                                axisLine={false}
                                                tickLine={false}
                                                unit="%"
                                            />
                                            <Tooltip
                                                formatter={(v: number | string | undefined) => [`${v ?? 0}%`, 'ROAS']}
                                                contentStyle={{ borderRadius: 12, border: '1px solid #F3F4F6', fontSize: 12 }}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="roas"
                                                stroke="#6366F1"
                                                strokeWidth={2}
                                                dot={false}
                                                activeDot={{ r: 4 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <NoDataPlaceholder />
                            )}
                        </DashboardWidget>
                        </ErrorBoundary>
                    </div>

                    {/* 비효율 광고 */}
                    <ErrorBoundary name="비효율 광고 감지">
                    <DashboardWidget
                        title="비효율 광고 감지"
                        subtitle="ROAS·CTR·CPA 기준 미달 캠페인 자동 탐지"
                    >
                        {inefficientAds.length > 0 ? (
                            <div className="mt-4 space-y-3">
                                {inefficientAds.map((ad: any, i: number) => (
                                    <div
                                        key={i}
                                        className={clsx(
                                            "p-5 rounded-2xl border",
                                            ad.severity === 'high'
                                                ? "bg-red-50 border-red-100"
                                                : "bg-amber-50 border-amber-100"
                                        )}
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <AlertTriangle className={clsx(
                                                        "w-4 h-4",
                                                        ad.severity === 'high' ? "text-red-500" : "text-amber-500"
                                                    )} />
                                                    <span className="font-bold text-gray-900 text-sm">{ad.campaign_name}</span>
                                                    <span className={clsx(
                                                        "text-[10px] font-black px-2 py-0.5 rounded",
                                                        ad.severity === 'high'
                                                            ? "bg-red-100 text-red-700"
                                                            : "bg-amber-100 text-amber-700"
                                                    )}>
                                                        {ad.severity === 'high' ? '심각' : '주의'}
                                                    </span>
                                                </div>
                                                <div className="flex gap-4 text-xs text-gray-500 mb-3">
                                                    <span>ROAS <strong className="text-gray-800">{ad.roas}%</strong></span>
                                                    <span>CTR <strong className="text-gray-800">{ad.ctr}%</strong></span>
                                                    <span>CPA <strong className="text-gray-800">₩{(ad.cpa ?? 0).toLocaleString()}</strong></span>
                                                    <span>지출 <strong className="text-gray-800">₩{(ad.spend ?? 0).toLocaleString()}</strong></span>
                                                </div>
                                                <div className="space-y-1">
                                                    {ad.issues?.map((issue: string, j: number) => (
                                                        <p key={j} className="text-xs text-red-700">• {issue}</p>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="text-right space-y-1 max-w-xs">
                                                {ad.recommendations?.map((rec: string, j: number) => (
                                                    <p key={j} className="text-xs text-gray-600 bg-white px-3 py-1.5 rounded-lg border border-gray-100">{rec}</p>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-10 text-center text-gray-400 text-sm">
                                <Target className="w-8 h-8 mx-auto mb-3 text-green-400" />
                                비효율 광고가 감지되지 않았습니다. 모든 캠페인이 기준을 충족합니다.
                            </div>
                        )}
                    </DashboardWidget>
                    </ErrorBoundary>

                    {/* 예산 재분배 */}
                    <ErrorBoundary name="예산 재분배 추천">
                    <DashboardWidget
                        title="예산 재분배 추천"
                        subtitle="ROAS 기반 최적 예산 배분 시나리오"
                    >
                        {budgetRecs.length > 0 ? (
                            <>
                                <div className="mt-4 grid grid-cols-3 gap-4 mb-6">
                                    <div className="bg-gray-50 rounded-2xl p-4 text-center">
                                        <p className="text-xs text-gray-400 mb-1">현재 총 예산</p>
                                        <p className="text-lg font-black text-gray-900 font-mono">
                                            ₩{(budgetSummary.current_total_budget ?? 0).toLocaleString()}
                                        </p>
                                    </div>
                                    <div className="bg-indigo-50 rounded-2xl p-4 text-center">
                                        <p className="text-xs text-indigo-400 mb-1">추천 총 예산</p>
                                        <p className="text-lg font-black text-indigo-700 font-mono">
                                            ₩{(budgetSummary.recommended_total_budget ?? 0).toLocaleString()}
                                        </p>
                                    </div>
                                    <div className={clsx(
                                        "rounded-2xl p-4 text-center",
                                        (budgetSummary.net_change ?? 0) <= 0 ? "bg-green-50" : "bg-amber-50"
                                    )}>
                                        <p className="text-xs text-gray-400 mb-1">예산 변화</p>
                                        <p className={clsx(
                                            "text-lg font-black font-mono",
                                            (budgetSummary.net_change ?? 0) <= 0 ? "text-green-700" : "text-amber-700"
                                        )}>
                                            {(budgetSummary.net_change ?? 0) > 0 ? '+' : ''}
                                            ₩{(budgetSummary.net_change ?? 0).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    {budgetRecs.map((rec: any, i: number) => (
                                        <div
                                            key={i}
                                            className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl hover:bg-gray-100/50 transition-all"
                                        >
                                            <div className="flex items-center gap-3">
                                                {rec.action === '증액' ? (
                                                    <ArrowUpRight className="w-4 h-4 text-green-500 shrink-0" />
                                                ) : rec.action === '감액' ? (
                                                    <ArrowDownRight className="w-4 h-4 text-red-500 shrink-0" />
                                                ) : (
                                                    <Minus className="w-4 h-4 text-gray-400 shrink-0" />
                                                )}
                                                <div>
                                                    <p className="text-sm font-bold text-gray-900">{rec.campaign_name}</p>
                                                    <p className="text-xs text-gray-400">{rec.reason}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className={clsx(
                                                    "text-sm font-black font-mono",
                                                    rec.action === '증액' ? "text-green-600"
                                                        : rec.action === '감액' ? "text-red-600"
                                                        : "text-gray-500"
                                                )}>
                                                    {rec.change}
                                                </p>
                                                <p className="text-xs text-gray-400">
                                                    ₩{(rec.recommended_spend ?? 0).toLocaleString()} 추천
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <NoDataPlaceholder />
                        )}
                    </DashboardWidget>
                    </ErrorBoundary>
                </>
            )}
        </div>
    );
}

/* ── 재사용 컴포넌트 ── */

interface AdsKpiCardProps {
    label: string;
    value: string;
    icon: React.ElementType;
    color: 'indigo' | 'green' | 'amber' | 'blue';
}

function AdsKpiCard({ label, value, icon: Icon, color }: AdsKpiCardProps) {
    const colors = {
        indigo: "bg-indigo-50 text-indigo-600",
        green:  "bg-green-50 text-green-600",
        amber:  "bg-amber-50 text-amber-600",
        blue:   "bg-blue-50 text-blue-600",
    };
    return (
        <div className="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-all">
            <div className={clsx("inline-flex p-2 rounded-xl mb-3", colors[color])}>
                <Icon className="w-5 h-5" />
            </div>
            <p className="text-2xl font-black text-gray-900 font-mono tracking-tighter">{value}</p>
            <p className="text-[11px] text-gray-400 mt-1 font-bold uppercase tracking-widest">{label}</p>
        </div>
    );
}

function NoDataPlaceholder() {
    return (
        <div className="py-12 text-center text-gray-400 text-sm">
            <TrendingDown className="w-8 h-8 mx-auto mb-3 text-gray-300" />
            광고 연동 후 데이터가 수집되면 표시됩니다.
        </div>
    );
}
