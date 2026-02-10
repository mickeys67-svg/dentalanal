"use client";

import React from 'react';
import { KPICard } from '@/components/dashboard/KPICard';
import { PerformanceChart } from '@/components/dashboard/PerformanceChart';
import { SOVChart } from '@/components/dashboard/SOVChart';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { useDashboard } from '@/hooks/useDashboard';
import { Loader2, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { DashboardKPI, Campaign } from '@/types';
import { translateMetric } from '@/lib/i18n';

const mockTrendData = [
    { name: '월', 광고비: 400000, 전환수: 12 },
    { name: '화', 광고비: 300000, 전환수: 10 },
    { name: '수', 광고비: 500000, 전환수: 18 },
    { name: '목', 광고비: 450000, 전환수: 15 },
    { name: '금', 광고비: 600000, 전환수: 22 },
    { name: '토', 광고비: 200000, 전환수: 8 },
    { name: '일', 광고비: 150000, 전환수: 5 },
];

const mockSOVData = [
    { name: '네이버', value: 45 },
    { name: '구글', value: 25 },
    { name: '메타', value: 20 },
    { name: '기타', value: 10 },
];

export default function DashboardPage() {
    const { summary, isLoading, error, refresh, isSyncing, startSync } = useDashboard();

    if (isLoading) {
        return (
            <div className="flex h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-3 text-gray-500 font-medium">성과 데이터를 불러오는 중...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-[80vh] flex-col items-center justify-center space-y-4">
                <p className="text-danger font-medium">데이터를 불러오는 중 오류가 발생했습니다.</p>
                <button
                    onClick={() => refresh()}
                    className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-white hover:bg-opacity-90 transition-colors"
                >
                    <RefreshCw className="h-4 w-4" /> 다시 시도
                </button>
            </div>
        );
    }

    // Use summary data if available, otherwise fall back to empty defaults
    const kpis = (summary?.kpis || []) as any[];
    const campaigns: Campaign[] = summary?.campaigns || [];

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">종합 성과 대시보드</h1>
                    <p className="text-gray-500">모든 채널의 마케팅 성과를 한눈에 파악하세요.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => startSync()}
                        disabled={isSyncing}
                        className="flex items-center gap-2 rounded-lg border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={clsx("h-4 w-4", isSyncing && "animate-spin")} />
                        {isSyncing ? '동기화 중...' : '전체 동기화'}
                    </button>
                    <button
                        onClick={() => refresh()}
                        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                        <RefreshCw className="h-4 w-4" /> 새로고침
                    </button>
                    <button className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-opacity-90 transition-all shadow-sm">
                        리포트 생성
                    </button>
                </div>
            </div>

            {/* KPI Section */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
                {kpis.map((kpi, index: number) => (
                    <KPICard
                        key={index}
                        title={translateMetric(kpi.title || kpi.label)}
                        value={kpi.value}
                        change={kpi.change}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                    />
                ))}
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <DashboardWidget
                    title="매체별 성과 트렌드"
                    subtitle="최근 7일간의 지표 변화"
                    className="lg:col-span-2"
                >
                    <div className="flex gap-2 justify-end mb-4">
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                            <span className="h-2 w-2 rounded-full bg-primary"></span> 광고비
                        </span>
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                            <span className="h-2 w-2 rounded-full bg-success"></span> 전환수
                        </span>
                    </div>
                    <PerformanceChart data={mockTrendData} />
                </DashboardWidget>

                <DashboardWidget title="매체별 비중 (SOV)">
                    <SOVChart data={summary?.sov_data || mockSOVData} />
                </DashboardWidget>
            </div>

            {/* Detailed Table */}
            <div className="rounded-xl border border-gray-100 bg-white shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-50 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-gray-900">캠페인별 성과 상세</h3>
                    <span className="text-xs text-gray-400">최근 7일 기준</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold">
                            <tr>
                                <th className="px-6 py-3">캠페인명</th>
                                <th className="px-6 py-3">매체</th>
                                <th className="px-6 py-3 text-right">광고비</th>
                                <th className="px-6 py-3 text-right">ROAS</th>
                                <th className="px-6 py-3 text-right">전환</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {campaigns.map((camp, index: number) => (
                                <tr key={index} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-900">{camp.name}</td>
                                    <td className="px-6 py-4">
                                        <span className={clsx(
                                            "rounded-md px-2 py-1 text-xs font-medium",
                                            camp.platform.includes('NAVER') ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"
                                        )}>
                                            {translateMetric(camp.platform)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">₩{camp.spend.toLocaleString()}</td>
                                    <td className="px-6 py-4 text-right text-success font-semibold">{camp.roas}%</td>
                                    <td className="px-6 py-4 text-right font-mono">{camp.conversions}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
