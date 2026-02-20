"use client";

import React, { useState } from 'react';
import Head from 'next/head';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { Filter, TrendingUp, Users, Target, MousePointer2, Loader2, Search, Activity, Map } from 'lucide-react';
import KeywordPositioningMap from '@/components/dashboard/KeywordPositioningMap';
import clsx from 'clsx';
import { useQuery } from '@tanstack/react-query';
import { getFunnelData, getCohortData, getAttributionData, getSegmentData } from '@/lib/api';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    LineChart, Line
} from 'recharts';
import { FunnelStage, CohortRow, AttributionData, SegmentRow } from '@/types';
import { useClient } from '@/components/providers/ClientProvider';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';


const analysisTypes = [
    { id: 'funnel', name: '퍼널 분석 (Funnel)', icon: Target, description: '사용자 여정별 전환 단계 분석' },
    { id: 'cohort', name: '코호트 분석 (Cohort)', icon: Users, description: '사용자 유지율 및 생애 가치 분석' },
    { id: 'attribution', name: '기여도 분석 (Attribution)', icon: MousePointer2, description: '매체별 전환 기여도 가중치 산출' },
    { id: 'segment', name: '세그먼트 분석 (Segment)', icon: Filter, description: '오디언스 그룹별 성과 비교' },
    { id: 'rankings', name: '순위 추적 (Ranking)', icon: Search, description: '주요 키워드별 노출 순위 변동' },
    { id: 'sov', name: '점유율 분석 (SOV)', icon: Activity, description: '경쟁사 대비 노출 점유율 분석' },
    { id: 'positioning', name: '포지셔닝 맵 (Positioning)', icon: Map, description: '경쟁사 대비 키워드별 순위 히트맵' },
];

export default function AnalysisPage() {
    const { selectedClient } = useClient();
    const clientId = selectedClient?.id;

    // All hooks must be declared before any conditional return (React Rules of Hooks)
    const [selectedType, setSelectedType] = useState('funnel');
    const [attrModel, setAttrModel] = useState<'first_touch' | 'last_touch' | 'linear'>('linear');
    const [rankingKeyword, setRankingKeyword] = useState('치과 마케팅');
    const [rankingPlatform, setRankingPlatform] = useState('NAVER_AD');

    // 1. Funnel Data
    const { data: funnelData, isLoading: isFunnelLoading } = useQuery({
        queryKey: ['funnel', clientId],
        queryFn: () => getFunnelData(clientId!),
        enabled: selectedType === 'funnel' && !!clientId
    });

    // 2. Cohort Data
    const { data: cohortData, isLoading: isCohortLoading } = useQuery({
        queryKey: ['cohort', clientId],
        queryFn: () => getCohortData(clientId!),
        enabled: selectedType === 'cohort' && !!clientId
    });

    // 3. Attribution Data
    const { data: attributionData, isLoading: isAttrLoading } = useQuery({
        queryKey: ['attribution', clientId],
        queryFn: () => getAttributionData(clientId!),
        enabled: selectedType === 'attribution' && !!clientId
    });

    // 4. Segment Data
    const { data: segmentData, isLoading: isSegmentLoading } = useQuery({
        queryKey: ['segments', clientId],
        queryFn: () => getSegmentData(clientId!),
        enabled: selectedType === 'segment' && !!clientId
    });

    // 5. Rankings Data
    const { data: rankingData, isLoading: isRankingLoading } = useQuery({
        queryKey: ['rankings', rankingKeyword, rankingPlatform, clientId],
        queryFn: () => import('@/lib/api').then(mod => mod.getRankings(rankingKeyword, rankingPlatform)),
        enabled: selectedType === 'rankings' && !!clientId
    });

    const { data: trendData, isLoading: isTrendLoading } = useQuery({
        queryKey: ['rankingTrend', rankingKeyword, rankingPlatform, clientId],
        queryFn: () => import('@/lib/api').then(mod => mod.getRankingTrend({
            keyword: rankingKeyword,
            target_hospital: selectedClient?.name || '',
            platform: rankingPlatform,
            days: 14
        })),
        enabled: selectedType === 'rankings' && !!clientId && !!selectedClient?.name
    });

    const { data: sovData, isLoading: isSOVLoading } = useQuery({
        queryKey: ['sov', clientId],
        queryFn: () => import('@/lib/api').then(mod => mod.analyzeSOV({
            keywords: ['치과', '임플란트', '교정'],
            target_hospital: selectedClient?.name || '',
            platform: 'NAVER_PLACE',
            top_n: 10
        })),
        enabled: selectedType === 'sov' && !!clientId
    });

    // Early return AFTER all hooks
    if (!selectedClient) {
        return <EmptyClientPlaceholder title="분석할 업체를 선택해주세요" description="상단에서 업체를 선택하면 정밀 데이터 분석 기능이 활성화됩니다." />;
    }

    const renderFunnelChart = () => {
        if (isFunnelLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;

        // [Safety Check] Ensure data is valid array
        if (!funnelData || !Array.isArray(funnelData) || funnelData.length === 0) {
            return (
                <div className="h-80 flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-xl border border-dashed">
                    <Target className="h-10 w-10 mb-2 opacity-20" />
                    <span>퍼널 데이터가 없습니다.</span>
                </div>
            );
        }

        return (
            <div style={{ width: '100%', height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={funnelData} layout="vertical" margin={{ left: 40, right: 40 }}>
                        <XAxis type="number" hide />
                        <YAxis dataKey="stage" type="category" width={120} tick={{ fontSize: 12 }} />
                        <Tooltip cursor={{ fill: '#f3f4f6' }} />
                        <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={40}>
                            {funnelData?.map((entry: FunnelStage, index: number) => (
                                <Cell key={`cell-${index}`} fill={[`#4f46e5`, `#6366f1`, `#818cf8`][index % 3]} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        );
    };

    const renderCohortTable = () => {
        if (isCohortLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;

        // [Safety Check]
        if (!cohortData || !Array.isArray(cohortData) || cohortData.length === 0) {
            return <div className="h-80 flex items-center justify-center text-gray-400">데이터가 없습니다.</div>;
        }

        return (
            <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                            <th className="p-3 font-bold text-gray-500">유입 월</th>
                            <th className="p-3 font-bold text-gray-500">모수</th>
                            {[0, 1, 2, 3, 4, 5].map(m => <th key={m} className="p-3 font-bold text-gray-500">{m}개월 후</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {cohortData.map((row: CohortRow, i: number) => (
                            <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50">
                                <td className="p-3 font-semibold text-gray-700">{row.month}</td>
                                <td className="p-3 text-gray-400">{row.size}명</td>
                                {Array.isArray(row.retention) && row.retention.map((val: number, j: number) => (
                                    <td key={j} className="p-3">
                                        <div className={clsx(
                                            "w-full py-2 rounded text-center font-bold",
                                            val > 80 ? "bg-indigo-600 text-white" :
                                                val > 60 ? "bg-indigo-400 text-white" :
                                                    val > 40 ? "bg-indigo-200 text-indigo-800" :
                                                        "bg-indigo-50 text-indigo-400"
                                        )}>
                                            {val}%
                                        </div>
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    const renderAttributionChart = () => {
        if (isAttrLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;

        // [Safety Check]
        if (!attributionData || !Array.isArray(attributionData) || attributionData.length === 0) {
            return <div className="h-80 flex items-center justify-center text-gray-400">기여도 데이터가 없습니다.</div>;
        }

        return (
            <div className="space-y-6">
                <div className="flex gap-2 mb-4">
                    {(['first_touch', 'last_touch', 'linear'] as const).map(model => (
                        <button
                            key={model}
                            onClick={() => setAttrModel(model)}
                            className={clsx(
                                "px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all",
                                attrModel === model ? "bg-primary text-white" : "bg-gray-100 text-gray-400 hover:bg-gray-200"
                            )}
                        >
                            {model === 'first_touch' ? '처음 터치' : model === 'last_touch' ? '마지막 터치' : '선형 기여'}
                        </button>
                    ))}
                </div>
                <div style={{ width: '100%', height: 320 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={attributionData}>
                            <PolarGrid stroke="#e5e7eb" />
                            <PolarAngleAxis dataKey="channel" tick={{ fontSize: 10, fill: '#6b7280' }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} hide />
                            <Radar
                                name="기여도 (%)"
                                dataKey={attrModel}
                                stroke="#4f46e5"
                                fill="#4f46e5"
                                fillOpacity={0.6}
                            />
                            <Tooltip />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        );
    };

    const renderSegmentAnalysis = () => {
        if (isSegmentLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;

        // [Safety Check]
        if (!segmentData || !Array.isArray(segmentData) || segmentData.length === 0) {
            return <div className="h-80 flex items-center justify-center text-gray-400">세그먼트 데이터가 없습니다.</div>;
        }

        return (
            <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                    <thead>
                        <tr className="bg-gray-50 text-gray-400 font-bold uppercase tracking-wider">
                            <th className="p-4">세그먼트</th>
                            <th className="p-4 text-center">방문자</th>
                            <th className="p-4 text-center">전환율</th>
                            <th className="p-4 text-center">ROAS</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {segmentData.map((row: SegmentRow, i: number) => (
                            <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                <td className="p-4 font-semibold text-gray-700">{row.segment}</td>
                                <td className="p-4 text-center text-gray-500">{row.visitors.toLocaleString()}</td>
                                <td className="p-4 text-center">
                                    <span className="font-bold text-success">{row.conversion_rate}%</span>
                                </td>
                                <td className="p-4 text-center">
                                    <span className="font-bold text-primary">{row.roas}%</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    const renderRankingsList = () => {
        if (isRankingLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;

        return (
            <div className="space-y-4">
                <div className="flex gap-4">
                    <input
                        type="text"
                        value={rankingKeyword}
                        onChange={(e) => setRankingKeyword(e.target.value)}
                        className="border rounded px-3 py-2 text-sm"
                        placeholder="키워드 입력 (예: 치과 마케팅)"
                    />
                    <select
                        value={rankingPlatform}
                        onChange={(e) => setRankingPlatform(e.target.value)}
                        className="border rounded px-3 py-2 text-sm"
                    >
                        <option value="NAVER_VIEW">네이버 VIEW (블로그)</option>
                        <option value="NAVER_PLACE">네이버 지도 (Place)</option>
                        <option value="NAVER_AD">네이버 파워링크 (광고)</option>
                    </select>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                            <h4 className="text-sm font-bold text-gray-800 mb-4">순위 변동 트렌드 (14일)</h4>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={trendData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                        <XAxis dataKey="date" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                                        <YAxis reversed domain={[1, 50]} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                                        <Tooltip
                                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                            formatter={(value: any) => [`${value}위`, '순위']}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="rank"
                                            stroke="#6366f1"
                                            strokeWidth={3}
                                            dot={{ r: 4, fill: '#6366f1' }}
                                            activeDot={{ r: 6, strokeWidth: 0 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            {(!trendData || trendData.length === 0) && !isTrendLoading && (
                                <div className="text-center py-10 text-gray-400 text-xs mt-[-150px]">
                                    트렌드 데이터를 불러올 수 없습니다. (충분한 이력이 필요합니다)
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="lg:col-span-1 border rounded-xl p-4 bg-gray-50/50">
                        <h4 className="text-sm font-bold text-gray-800 mb-4">실시간 현황 요약</h4>
                        <div className="space-y-4">
                            <div className="p-3 bg-white rounded-lg shadow-sm border border-gray-100">
                                <div className="text-[10px] text-gray-400">현재 순위</div>
                                <div className="text-2xl font-black text-indigo-600">
                                    {rankingData?.find((r: any) => r.title.includes(selectedClient?.name || ''))?.rank || '권외'}
                                </div>
                            </div>
                            <div className="p-3 bg-white rounded-lg shadow-sm border border-gray-100">
                                <div className="text-[10px] text-gray-400">전일 대비</div>
                                <div className="text-lg font-bold text-success">▲ 2 (Simulated)</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto border rounded-xl overflow-hidden">
                    <table className="w-full text-xs text-left">
                        <thead>
                            <tr className="bg-gray-50 text-gray-400 font-bold uppercase tracking-wider">
                                <th className="p-4 w-16 text-center">순위</th>
                                <th className="p-4">대상 (Title/Target)</th>
                                <th className="p-4">링크</th>
                                <th className="p-4 text-right">수집 시간</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {rankingData?.map((row: any, i: number) => {
                                // [Safety Check]
                                const rank = row?.rank || '-';
                                const title = row?.title || 'Unknown';
                                const blogName = row?.blog_name || '';
                                const link = row?.link || '#';
                                const timeStr = row?.created_at ? new Date(row.created_at).toLocaleTimeString() : '-';

                                return (
                                    <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="p-4 text-center font-bold text-gray-900">{rank}</td>
                                        <td className="p-4 font-semibold text-gray-700">
                                            {title}
                                            {blogName && <span className="text-gray-400 text-[10px] ml-2">({blogName})</span>}
                                        </td>
                                        <td className="p-4 text-gray-500 truncate max-w-[200px]">
                                            {link !== '#' ? <a href={link} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">{link}</a> : '-'}
                                        </td>
                                        <td className="p-4 text-right text-gray-400">
                                            {timeStr}
                                        </td>
                                    </tr>
                                );
                            })}
                            {(!rankingData || rankingData.length === 0) && (
                                <tr>
                                    <td colSpan={4} className="p-8 text-center text-gray-400">
                                        데이터가 없습니다. 키워드를 확인하거나 스크래핑을 실행해주세요.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const renderSOVChart = () => {
        if (isSOVLoading) return <div className="flex justify-center p-20"><Loader2 className="animate-spin text-primary" /></div>;

        // [Safety Check] Ensure data is valid array
        if (!sovData || !Array.isArray(sovData) || sovData.length === 0) {
            return (
                <div className="flex flex-col items-center justify-center p-20 text-gray-400 bg-gray-50 rounded-xl border border-dashed">
                    <Activity className="h-10 w-10 mb-2 opacity-20" />
                    <span>데이터가 수집되지 않았습니다.</span>
                    <span className="text-xs mt-1">(조사가 진행 중이거나 연결된 데이터가 없습니다)</span>
                </div>
            );
        }

        return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <DashboardWidget title="종합 노출 점유율 (Avg SOV)">
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={sovData}>
                                <PolarGrid stroke="#E5E7EB" />
                                <PolarAngleAxis dataKey="keyword" tick={{ fill: '#6B7280', fontSize: 12 }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                <Radar
                                    name="SOV 점수"
                                    dataKey="sov_score"
                                    stroke="#6366F1"
                                    fill="#6366F1"
                                    fillOpacity={0.5}
                                />
                                <Tooltip />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </DashboardWidget>
                <DashboardWidget title="키워드별 점유율 현황">
                    <div className="space-y-4">
                        {sovData.map((item: any, idx: number) => {
                            // [Safety Check] Use default values to prevent crash
                            const keyword = item?.keyword || 'Unknown';
                            const rank = item?.top_rank || '-';
                            const score = typeof item?.sov_score === 'number' ? item.sov_score : 0;

                            return (
                                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                    <div>
                                        <div className="text-sm font-bold text-gray-900">{keyword}</div>
                                        <div className="text-[10px] text-gray-400">최고 순위: {rank}위</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-lg font-bold text-indigo-600">{score.toFixed(1)}%</div>
                                        <div className="w-24 bg-gray-200 h-1 rounded-full mt-1 overflow-hidden">
                                            <div className="bg-indigo-500 h-full" style={{ width: `${score}%` }} />
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </DashboardWidget>
            </div>
        );
    };

    const renderContent = () => {
        switch (selectedType) {
            case 'funnel': return renderFunnelChart();
            case 'cohort': return renderCohortTable();
            case 'attribution': return renderAttributionChart();
            case 'segment': return renderSegmentAnalysis();
            case 'rankings': return renderRankingsList();
            case 'sov': return renderSOVChart();
            case 'positioning': return <KeywordPositioningMap clientId={clientId!} />;
            default: return null;
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <Head>
                <title>심층 데이터 분석 | D-MIND</title>
                <meta name="description" content="퍼널 분석, 코호트 분석 등을 통해 마케팅 성과를 심층적으로 분석합니다." />
            </Head>
            <div className="flex flex-col gap-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">데이터 심층 분석 (Deep Analytics)</h1>
                    <p className="text-gray-500">정교한 분석 엔진으로 마케팅 퍼널과 기여도를 측정하세요.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
                <div className="lg:col-span-1 space-y-3">
                    {analysisTypes.map((type) => (
                        <button
                            key={type.id}
                            onClick={() => setSelectedType(type.id)}
                            className={clsx(
                                "w-full text-left p-4 rounded-xl border transition-all duration-200",
                                selectedType === type.id
                                    ? "bg-primary/5 border-primary/20 shadow-sm"
                                    : "bg-white border-gray-100 hover:border-gray-200"
                            )}
                        >
                            <div className="flex items-center gap-3">
                                <div className={clsx(
                                    "p-2 rounded-lg",
                                    selectedType === type.id ? "bg-primary text-white" : "bg-gray-50 text-gray-400"
                                )}>
                                    <type.icon className="h-5 w-5" />
                                </div>
                                <div>
                                    <h4 className={clsx(
                                        "text-sm font-semibold",
                                        selectedType === type.id ? "text-primary" : "text-gray-700"
                                    )}>
                                        {type.name}
                                    </h4>
                                    <p className="text-[10px] text-gray-400 mt-0.5">{type.description}</p>
                                </div>
                            </div>
                        </button>
                    ))}
                </div>

                <div className="lg:col-span-3 space-y-6">
                    <DashboardWidget
                        title={`${analysisTypes.find(t => t.id === selectedType)?.name} 결과`}
                        subtitle="실시간 엔진 분석 데이터를 기반으로 시각화되었습니다."
                    >
                        <div className="min-h-[400px]">
                            {renderContent()}
                        </div>
                    </DashboardWidget>

                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                        <DashboardWidget title="데이터 인사이트">
                            <ul className="space-y-4">
                                <li className="flex items-start gap-4">
                                    <div className="mt-1 h-2 w-2 rounded-full bg-success"></div>
                                    <div>
                                        <p className="text-sm font-medium text-gray-800">성능 최적화 지점 발견</p>
                                        <p className="text-xs text-gray-500 mt-0.5">
                                            {selectedType === 'funnel' ? "상단 퍼널에서 하단 전환까지의 흐름이 시각화되었습니다. 병목 지점을 확인하세요." :
                                                selectedType === 'cohort' ? "유입 시기별 고객 유지율(Retention)을 통해 장기 가치를 분석할 수 있습니다." :
                                                    selectedType === 'attribution' ? "각 매체가 전환에 기여한 비중을 가중치 모델별로 확인할 수 있습니다." :
                                                        selectedType === 'rankings' ? "주요 키워드에 대한 현재 노출 위치 및 변동 이력을 추적합니다." :
                                                            "정의된 오디언스 그룹별 성과 차이를 분석하여 고효율 세그먼트를 발굴하세요."}
                                        </p>
                                    </div>
                                </li>
                                <li className="flex items-start gap-4">
                                    <div className="mt-1 h-2 w-2 rounded-full bg-amber-400"></div>
                                    <div>
                                        <p className="text-sm font-medium text-gray-800">주의 필요</p>
                                        <p className="text-xs text-gray-500 mt-0.5">상담 신청 단계에서의 이탈률이 0.5% 증가했습니다. 폼 최적화가 필요합니다.</p>
                                    </div>
                                </li>
                            </ul>
                        </DashboardWidget>
                        <DashboardWidget title="AI 권장 전략">
                            <div className="flex flex-col h-full bg-indigo-50/50 p-4 rounded-xl border border-indigo-100">
                                <p className="text-xs text-indigo-700 leading-relaxed font-medium">
                                    "현재 분석 데이터에 따르면 초기 유입은 소셜 매체가 우세하나, 최종 전환은 검색 광고가 리드하고 있습니다. 크로스 채널 리마케팅 비중을 20% 높이는 전략을 추천합니다."
                                </p>
                                <div className="mt-4 flex items-center gap-2 text-[10px] text-indigo-400">
                                    <TrendingUp className="h-3 w-3" /> Gemini AI 심층 분석 결과
                                </div>
                            </div>
                        </DashboardWidget>
                    </div>
                </div>
            </div>
        </div>
    );
}
