"use client";

import React, { useState } from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { Filter, BarChart2, TrendingUp, Users, Target, MousePointer2, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { useQuery } from '@tanstack/react-query';
import { getFunnelData, getCohortData, getAttributionData, getSegmentData } from '@/lib/api';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend
} from 'recharts';
import { FunnelStage, CohortRow, AttributionData, SegmentRow } from '@/types';

const DEFAULT_CLIENT_ID = "00000000-0000-0000-0000-000000000000";

const analysisTypes = [
    { id: 'funnel', name: '퍼널 분석 (Funnel)', icon: Target, description: '사용자 여정별 전환 단계 분석' },
    { id: 'cohort', name: '코호트 분석 (Cohort)', icon: Users, description: '사용자 유지율 및 생애 가치 분석' },
    { id: 'attribution', name: '기여도 분석 (Attribution)', icon: MousePointer2, description: '매체별 전환 기여도 가중치 산출' },
    { id: 'segment', name: '세그먼트 분석 (Segment)', icon: Filter, description: '오디언스 그룹별 성과 비교' },
    { id: 'rankings', name: '키워드 순위 (Rankings)', icon: TrendingUp, description: '네이버 실시간 노출 순위 모니터링' },
];

export default function AnalysisPage() {
    const [selectedType, setSelectedType] = useState('funnel');
    const [attrModel, setAttrModel] = useState<'first_touch' | 'last_touch' | 'linear'>('linear');

    // 1. Funnel Data
    const { data: funnelData, isLoading: isFunnelLoading } = useQuery({
        queryKey: ['funnel', DEFAULT_CLIENT_ID],
        queryFn: () => getFunnelData(DEFAULT_CLIENT_ID),
        enabled: selectedType === 'funnel'
    });

    // 2. Cohort Data
    const { data: cohortData, isLoading: isCohortLoading } = useQuery({
        queryKey: ['cohort', DEFAULT_CLIENT_ID],
        queryFn: () => getCohortData(DEFAULT_CLIENT_ID),
        enabled: selectedType === 'cohort'
    });

    // 3. Attribution Data
    const { data: attributionData, isLoading: isAttrLoading } = useQuery({
        queryKey: ['attribution', DEFAULT_CLIENT_ID],
        queryFn: () => getAttributionData(DEFAULT_CLIENT_ID),
        enabled: selectedType === 'attribution'
    });

    // 4. Segment Data
    const { data: segmentData, isLoading: isSegmentLoading } = useQuery({
        queryKey: ['segments', DEFAULT_CLIENT_ID],
        queryFn: () => getSegmentData(DEFAULT_CLIENT_ID),
        enabled: selectedType === 'segment'
    });

    // 5. Rankings Data (New)
    const [rankingKeyword, setRankingKeyword] = useState('치과 마케팅');
    const [rankingPlatform, setRankingPlatform] = useState('NAVER_AD');

    const { data: rankingData, isLoading: isRankingLoading } = useQuery({
        queryKey: ['rankings', rankingKeyword, rankingPlatform],
        queryFn: () => import('@/lib/api').then(mod => mod.getRankings(rankingKeyword, rankingPlatform)),
        enabled: selectedType === 'rankings'
    });

    const renderFunnelChart = () => {
        if (isFunnelLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;
        return (
            <ResponsiveContainer width="100%" height={320}>
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
        );
    };

    const renderCohortHeatmap = () => {
        if (isCohortLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;
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
                        {cohortData?.map((row: CohortRow, i: number) => (
                            <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50">
                                <td className="p-3 font-semibold text-gray-700">{row.month}</td>
                                <td className="p-3 text-gray-400">{row.size}명</td>
                                {row.retention.map((val: number, j: number) => (
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
                <ResponsiveContainer width="100%" height={320}>
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
        );
    };

    const renderSegmentTable = () => {
        if (isSegmentLoading) return <div className="h-80 flex items-center justify-center"><Loader2 className="animate-spin text-primary" /></div>;
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
                        {segmentData?.map((row: SegmentRow, i: number) => (
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

    const renderRankingTable = () => {
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

                <div className="overflow-x-auto border rounded-lg">
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
                            {rankingData?.map((row: any, i: number) => (
                                <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                    <td className="p-4 text-center font-bold text-gray-900">{row.rank}</td>
                                    <td className="p-4 font-semibold text-gray-700">
                                        {row.title}
                                        {row.blog_name && <span className="text-gray-400 text-[10px] ml-2">({row.blog_name})</span>}
                                    </td>
                                    <td className="p-4 text-gray-500 truncate max-w-[200px]">
                                        {row.link ? <a href={row.link} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">{row.link}</a> : '-'}
                                    </td>
                                    <td className="p-4 text-right text-gray-400">
                                        {new Date(row.created_at).toLocaleTimeString()}
                                    </td>
                                </tr>
                            ))}
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

    const renderContent = () => {
        switch (selectedType) {
            case 'funnel': return renderFunnelChart();
            case 'cohort': return renderCohortHeatmap();
            case 'attribution': return renderAttributionChart();
            case 'segment': return renderSegmentTable();
            case 'rankings': return renderRankingTable();
            default: return null;
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
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
                                            {selectedType === 'funnel' ? "클릭 대비 전환 효율이 지난 달보다 15% 개선되었습니다." :
                                                selectedType === 'cohort' ? "2월 유입 고객의 리텐션이 다른 달보다 견고합니다." :
                                                    selectedType === 'attribution' ? "초기 인지도 형성에 인스타그램이 45% 기여하고 있습니다." :
                                                        selectedType === 'rankings' ? "경쟁사 대비 상위 노출 점유율이 20% 상승했습니다." :
                                                            "재방문자의 전환율이 신규 방문자보다 3배 이상 높습니다."}
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
