"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useParams, useRouter } from 'next/navigation';
import { Loader2, ArrowLeft, Download, Share2, AlertCircle, Target } from 'lucide-react';
import { KPICard } from '@/components/dashboard/KPICard';
import { PerformanceChart } from '@/components/dashboard/PerformanceChart';

import {
    ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
    Tooltip as RechartsTooltip, Cell, BarChart as RechartsBarChart, Bar as RechartsBar,
    XAxis as RechartsXAxis, YAxis as RechartsYAxis, LineChart, Line, CartesianGrid, Legend
} from 'recharts';

export default function ReportDetailPage() {
    const { id } = useParams();
    const router = useRouter();

    const { data: report, isLoading, error } = useQuery({
        queryKey: ['report', id],
        queryFn: async () => {
            const response = await api.get(`/api/v1/reports/detail/${id}`);
            return response.data;
        },
        enabled: !!id,
    });

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error || !report) {
        return (
            <div className="p-8 text-center text-red-500">
                리포트를 불러오는 중 오류가 발생했습니다.
            </div>
        );
    }

    if (report.status === "PENDING") {
        return (
            <div className="flex flex-col h-screen items-center justify-center space-y-4">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
                <div className="text-center">
                    <h2 className="text-xl font-bold text-gray-900">리포트 생성 중...</h2>
                    <p className="text-gray-500">데이터를 분석하여 리포트를 생성하고 있습니다. 잠시만 기다려 주세요.</p>
                </div>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                    새로고침
                </button>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-10 py-4 border-b border-gray-100 print:hidden">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">{report.title}</h1>
                        <p className="text-xs text-gray-500">생성일: {new Date(report.created_at).toLocaleString()}</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={async () => {
                            try {
                                const response = await api.get(`/api/v1/reports/pdf/${report.id}`, {
                                    responseType: 'blob'
                                });
                                const blob = new Blob([response.data], { type: 'application/pdf' });
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `report_${report.id}.pdf`;
                                document.body.appendChild(a);
                                a.click();
                                window.URL.revokeObjectURL(url);
                                document.body.removeChild(a);
                            } catch (error) {
                                console.error('PDF download failed:', error);
                                toast.error('PDF 다운로드에 실패했습니다.');
                            }
                        }}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-all font-medium"
                    >
                        <Download className="w-4 h-4" /> PDF 다운로드
                    </button>
                    <button
                        onClick={() => {
                            navigator.clipboard.writeText(window.location.href);
                            toast.success('공유 링크가 클립보드에 복사되었습니다.');
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-opacity-90 transition-all font-medium shadow-sm"
                    >
                        <Share2 className="w-4 h-4" /> 리포트 공유
                    </button>
                </div>
            </div>

            {/* Print Header (Only visible when printing) */}
            <div className="hidden print:block text-center border-b-2 border-gray-900 pb-8 mb-10">
                <div className="text-3xl font-black mb-2">DIGITAL AD PERFORMANCE REPORT</div>
                <div className="text-sm text-gray-400">{report.title} | {new Date(report.created_at).toLocaleDateString()}</div>
                <div className="text-xs mt-4 text-gray-400">Copyright © 2024 Dental Analytics All Right Reserved.</div>
            </div>

            {/* Dynamic Widgets */}
            <div className="space-y-8">
                {report.data?.widgets?.map((widget: any, index: number) => (
                    <div key={index} className="animate-in fade-in slide-in-from-bottom-4 duration-700" style={{ animationDelay: `${index * 100}ms` }}>
                        {renderWidget(widget)}
                    </div>
                ))}
            </div>
        </div>
    );
}

function renderWidget(widget: any) {
    switch (widget.type) {
        case "KPI_GROUP":
            return (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {widget.data?.map((kpi: any, i: number) => (
                        <KPICard
                            key={i}
                            title={kpi.label}
                            value={kpi.value}
                            change={0}
                            prefix={kpi.prefix}
                        />
                    ))}
                </div>
            );
        case "BENCHMARK":
            const bench = widget.data;
            if (!bench) return null;
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm space-y-6">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-bold text-gray-900">{widget.title || "업종별 벤치마크 비교"}</h3>
                        <span className="text-xs bg-indigo-50 text-primary px-3 py-1 rounded-full font-semibold">업종: {bench.industry}</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {renderBenchMetric("클릭률 (CTR)", bench.client_kpis?.ctr, bench.industry_avg?.avg_ctr, "%")}
                        {renderBenchMetric("클릭당 비용 (CPC)", bench.client_kpis?.cpc, bench.industry_avg?.avg_cpc, "원")}
                        {renderBenchMetric("전환율 (CVR)", bench.client_kpis?.cvr, bench.industry_avg?.avg_cvr, "%")}
                    </div>
                </div>
            );
        case "SOV":
            const sovData = widget.data?.keyword_details || [];
            if (!sovData.length) return null;
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "키워드별 노출 점유율 (SOV)"}</h3>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={sovData.map((d: any) => ({ keyword: d.keyword, sov: d.sov }))}>
                                    <PolarGrid stroke="#E5E7EB" />
                                    <PolarAngleAxis dataKey="keyword" tick={{ fill: '#6B7280', fontSize: 10 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} hide />
                                    <Radar name="SOV 점수" dataKey="sov" stroke="#6366F1" fill="#6366F1" fillOpacity={0.5} />
                                    <RechartsTooltip />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="space-y-4">
                            {sovData.map((item: any, idx: number) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                    <div className="text-sm font-bold text-gray-900">{item.keyword}</div>
                                    <div className="text-right">
                                        <div className="text-lg font-bold text-indigo-600 font-mono">{item.sov.toFixed(1)}%</div>
                                        <div className="w-24 bg-gray-200 h-1 rounded-full mt-1 overflow-hidden">
                                            <div className="bg-indigo-500 h-full" style={{ width: `${item.sov}%` }} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            );
        case "COMPETITORS":
            const competitors = widget.data?.competitors || [];
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || `경쟁사 점유율 분석 (${widget.data?.keyword || ''})`}</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead>
                                <tr className="text-gray-400 font-bold border-b border-gray-50 uppercase tracking-tighter text-[10px]">
                                    <th className="pb-4">병원명</th>
                                    <th className="pb-4">노출 횟수</th>
                                    <th className="pb-4">평균 순위</th>
                                    <th className="pb-4">점유율</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {competitors.map((c: any, i: number) => (
                                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                                        <td className="py-4 font-bold text-gray-800">{c.name}</td>
                                        <td className="py-4 text-gray-500 font-mono">{c.rank_count}회</td>
                                        <td className="py-4 text-gray-500 font-mono">{c.avg_rank.toFixed(1)}위</td>
                                        <td className="py-4 font-bold text-primary font-mono">{c.share.toFixed(1)}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            );
        case "RANKINGS":
            const rankings = widget.data || [];
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "주요 키워드 노출 순위 리스트"}</h3>
                    <div className="space-y-3">
                        {rankings.map((r: any, i: number) => (
                            <div key={i} className="flex items-center justify-between p-4 border border-gray-50 rounded-xl hover:shadow-sm transition-all group">
                                <div className="flex items-center gap-4">
                                    <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-primary font-black text-xs">
                                        {r.rank}
                                    </div>
                                    <div className="font-bold text-gray-800 group-hover:text-primary transition-colors">{r.title}</div>
                                </div>
                                <div className="text-[10px] text-gray-400">수집: {new Date(r.created_at).toLocaleTimeString()}</div>
                            </div>
                        ))}
                    </div>
                </div>
            );
        case "FUNNEL":
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "퍼널 분석 데이터"}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {widget.data?.map((f: any, i: number) => (
                            <div key={i} className="p-6 bg-gray-50 rounded-xl relative overflow-hidden group">
                                <div className="text-xs text-gray-400 mb-1">{f.stage}</div>
                                <div className="text-2xl font-bold text-gray-900">{f.value.toLocaleString()}</div>
                                {f.rate && <div className="text-[10px] font-bold text-indigo-500 mt-2">{f.unit}: {f.rate}%</div>}
                                <div className="absolute right-0 bottom-0 opacity-10 group-hover:opacity-20 transition-opacity">
                                    <Target className="w-16 h-16 -mr-4 -mb-4" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            );
        case "LINE_CHART":
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "성과 추이 일자별 리포트"}</h3>
                    <div className="h-80">
                        <PerformanceChart data={widget.data} title={widget.title || "성과 추이"} />
                    </div>
                </div>
            );
        case "TREND_CHART": {
            const trendData = widget.data?.data || [];
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "광고 성과 일별 트렌드"}</h3>
                    {trendData.length === 0 ? (
                        <div className="h-[280px] flex items-center justify-center text-gray-400 text-sm">수집된 트렌드 데이터가 없습니다.</div>
                    ) : (
                        <div className="h-[280px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={trendData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                                    <RechartsXAxis dataKey="date" tick={{ fontSize: 11, fill: '#9CA3AF' }} tickFormatter={(v) => v.slice(5)} />
                                    <RechartsYAxis yAxisId="left" tick={{ fontSize: 11, fill: '#9CA3AF' }} tickFormatter={(v) => `${(v / 10000).toFixed(0)}만`} />
                                    <RechartsYAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: '#9CA3AF' }} />
                                    <RechartsTooltip
                                        contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
                                        formatter={(value: any, name: string | undefined) => [
                                            name === 'spend' ? `₩${Number(value).toLocaleString()}` : value,
                                            name === 'spend' ? '광고비' : '전환수'
                                        ]}
                                    />
                                    <Legend formatter={(v) => v === 'spend' ? '광고비' : '전환수'} />
                                    <Line yAxisId="left" type="monotone" dataKey="spend" stroke="#6366F1" strokeWidth={2} dot={false} />
                                    <Line yAxisId="right" type="monotone" dataKey="conversions" stroke="#10B981" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
            );
        }
        case "ROI_COMPARISON": {
            const campaigns = widget.data?.campaigns || [];
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "캠페인별 ROAS 비교"}</h3>
                    {campaigns.length === 0 ? (
                        <div className="text-center text-gray-400 text-sm py-10">캠페인 데이터가 없습니다.</div>
                    ) : (
                        <>
                            <div className="h-[240px] mb-6">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RechartsBarChart data={campaigns.slice(0, 6)} layout="vertical" margin={{ left: 80, right: 40 }}>
                                        <RechartsXAxis type="number" tick={{ fontSize: 11, fill: '#9CA3AF' }} tickFormatter={(v) => `${v}%`} />
                                        <RechartsYAxis type="category" dataKey="campaign_name" tick={{ fontSize: 10, fill: '#6B7280' }} width={80} />
                                        <RechartsTooltip
                                            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
                                            formatter={(value: any) => [`${value}%`, 'ROAS']}
                                        />
                                        <RechartsBar dataKey="roas" fill="#6366F1" radius={[0, 4, 4, 0]}>
                                            {campaigns.slice(0, 6).map((_: any, idx: number) => (
                                                <Cell key={idx} fill={idx === 0 ? '#6366F1' : idx < 3 ? '#818CF8' : '#C7D2FE'} />
                                            ))}
                                        </RechartsBar>
                                    </RechartsBarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left">
                                    <thead>
                                        <tr className="text-gray-400 font-bold border-b border-gray-50 uppercase tracking-tighter text-[10px]">
                                            <th className="pb-3">캠페인명</th>
                                            <th className="pb-3">플랫폼</th>
                                            <th className="pb-3">ROAS</th>
                                            <th className="pb-3">광고비</th>
                                            <th className="pb-3">전환수</th>
                                            <th className="pb-3">CPA</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {campaigns.map((c: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50 transition-colors">
                                                <td className="py-3 font-bold text-gray-800 text-xs max-w-[160px] truncate">{c.campaign_name}</td>
                                                <td className="py-3 text-gray-400 text-xs">{c.platform}</td>
                                                <td className="py-3 font-bold text-indigo-600 font-mono">{c.roas}%</td>
                                                <td className="py-3 text-gray-500 font-mono text-xs">₩{Number(c.total_spend).toLocaleString()}</td>
                                                <td className="py-3 text-gray-500 font-mono text-xs">{c.total_conversions}건</td>
                                                <td className="py-3 text-gray-500 font-mono text-xs">₩{Number(c.cpa).toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </div>
            );
        }
        case "COHORT": {
            const cohorts: Array<{ month: string; size: number; retention: number[] }> = widget.data?.cohorts || [];
            return (
                <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">{widget.title || "고객 코호트 리텐션 분석"}</h3>
                    {cohorts.length === 0 ? (
                        <div className="text-center text-gray-400 text-sm py-10">코호트 분석을 위한 리드 데이터가 없습니다.</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead>
                                    <tr className="text-gray-400 font-bold border-b border-gray-100 text-[10px] uppercase tracking-wider">
                                        <th className="pb-3 pr-4">코호트</th>
                                        <th className="pb-3 pr-4">규모</th>
                                        {[0, 1, 2, 3, 4, 5].map(m => (
                                            <th key={m} className="pb-3 pr-3 text-center">{m}M</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {cohorts.map((c, i) => (
                                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                                            <td className="py-3 pr-4 font-bold text-gray-700 text-xs">{c.month}</td>
                                            <td className="py-3 pr-4 text-gray-500 font-mono text-xs">{c.size}명</td>
                                            {[0, 1, 2, 3, 4, 5].map(m => {
                                                const val = c.retention[m];
                                                const opacity = val != null ? Math.max(0.1, val / 100) : 0;
                                                return (
                                                    <td key={m} className="py-3 pr-3 text-center">
                                                        {val != null ? (
                                                            <span
                                                                className="inline-block px-2 py-1 rounded text-xs font-mono font-bold"
                                                                style={{
                                                                    backgroundColor: `rgba(99, 102, 241, ${opacity})`,
                                                                    color: opacity > 0.5 ? 'white' : '#4B5563'
                                                                }}
                                                            >
                                                                {val}%
                                                            </span>
                                                        ) : (
                                                            <span className="text-gray-200 text-xs">—</span>
                                                        )}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            );
        }
        case "AI_DIAGNOSIS":
            return (
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-8 rounded-2xl border border-indigo-100 shadow-sm relative overflow-hidden break-inside-avoid">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-200/20 rounded-full -mr-16 -mt-16 blur-3xl"></div>
                    <div className="flex items-center gap-2 mb-6 text-primary">
                        <div className="p-2 bg-white rounded-lg shadow-sm">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-bold">Gemini AI 마케팅 정밀 진단</h3>
                    </div>
                    <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-white/40 prose max-w-none">
                        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed font-sans text-sm md:text-base">
                            {widget.data?.content}
                        </div>
                    </div>
                </div>
            );
        default:
            return (
                <div className="p-6 bg-gray-50 rounded-xl border border-dashed border-gray-200 text-center text-gray-400">
                    지원되지 않는 위젯 타입입니다: {widget.type}
                </div>
            );
    }
}

function renderBenchMetric(label: string, clientVal: number, avgVal: number, unit: string) {
    const diff = clientVal - avgVal;
    const isGood = label.includes("CPC") ? diff < 0 : diff > 0;

    return (
        <div className="space-y-3">
            <p className="text-sm font-medium text-gray-500">{label}</p>
            <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-gray-900">{clientVal.toLocaleString()}{unit}</span>
                <span className={`text-xs font-bold mb-1 px-1.5 py-0.5 rounded ${isGood ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {diff > 0 ? '+' : ''}{diff.toLocaleString()}{unit}
                </span>
            </div>
            <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full ${isGood ? 'bg-success' : 'bg-primary'}`}
                    style={{ width: `${Math.min((clientVal / (avgVal * 1.5)) * 100, 100)}%` }}
                ></div>
            </div>
            <p className="text-[10px] text-gray-400">시장 평균: {avgVal.toLocaleString()}{unit}</p>
        </div>
    );
}
