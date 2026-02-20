'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { BarChart3, TrendingUp, Calendar, FileText, Loader2, AlertCircle, Building2 } from 'lucide-react';

interface PortalReport {
    id: string;
    title: string;
    period_start: string | null;
    period_end: string | null;
    generated_at: string | null;
    data_summary: {
        kpis?: Array<{ label: string; value: number | string; unit?: string }>;
        funnel?: Array<{ stage: string; value: number }>;
    };
}

interface PortalData {
    client: { id: string; name: string; industry: string | null };
    expires_at: string;
    reports: PortalReport[];
}

export default function PortalPage() {
    const params = useParams();
    const token = params.token as string;
    const [data, setData] = useState<PortalData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || '';
        fetch(`${backendUrl}/api/v1/reports/portal/${token}`)
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || '유효하지 않은 링크입니다.');
                }
                return res.json();
            })
            .then(setData)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, [token]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center space-y-3">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
                    <p className="text-gray-600 font-medium">{error}</p>
                    <p className="text-sm text-gray-400">링크가 만료되었거나 잘못된 주소입니다.</p>
                </div>
            </div>
        );
    }

    if (!data) return null;

    const expiresDate = new Date(data.expires_at).toLocaleDateString('ko-KR');

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50/30">
            {/* 헤더 */}
            <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                            <BarChart3 className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <span className="font-bold text-gray-900">D-MIND</span>
                            <span className="ml-2 text-xs text-gray-400">클라이언트 포털</span>
                        </div>
                    </div>
                    <div className="text-xs text-gray-400">
                        링크 만료: {expiresDate}
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">
                {/* 클라이언트 헤딩 */}
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-indigo-100 rounded-2xl flex items-center justify-center">
                        <Building2 className="w-7 h-7 text-indigo-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-extrabold text-gray-900">{data.client.name}</h1>
                        <p className="text-sm text-gray-400">{data.client.industry || '업종 미분류'} · 마케팅 성과 리포트</p>
                    </div>
                </div>

                {/* 리포트 목록 */}
                {data.reports.length === 0 ? (
                    <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center">
                        <FileText className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                        <p className="text-gray-400">아직 완료된 리포트가 없습니다.</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {data.reports.map(report => (
                            <ReportCard key={report.id} report={report} />
                        ))}
                    </div>
                )}

                <footer className="text-center text-xs text-gray-300 pt-8 pb-4">
                    Powered by D-MIND · 이 페이지는 읽기 전용입니다
                </footer>
            </main>
        </div>
    );
}

function ReportCard({ report }: { report: PortalReport }) {
    const kpis = report.data_summary?.kpis ?? [];
    const funnel = report.data_summary?.funnel ?? [];

    const period = report.period_start && report.period_end
        ? `${report.period_start} ~ ${report.period_end}`
        : '기간 정보 없음';

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {/* 리포트 헤더 */}
            <div className="px-6 py-5 border-b border-gray-50 flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-lg font-bold text-gray-900">{report.title}</h2>
                    <div className="flex items-center gap-4 mt-1">
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                            <Calendar className="w-3 h-3" /> {period}
                        </span>
                        {report.generated_at && (
                            <span className="flex items-center gap-1 text-xs text-gray-400">
                                <TrendingUp className="w-3 h-3" />
                                생성: {new Date(report.generated_at).toLocaleDateString('ko-KR')}
                            </span>
                        )}
                    </div>
                </div>
                <span className="px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-semibold rounded-full shrink-0">
                    완료
                </span>
            </div>

            <div className="px-6 py-6 space-y-6">
                {/* KPI 그리드 */}
                {kpis.length > 0 && (
                    <div>
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">핵심 지표</h3>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {kpis.map((kpi, i) => (
                                <div key={i} className="bg-gray-50 rounded-xl p-4">
                                    <div className="text-lg font-bold text-gray-900">
                                        {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
                                        {kpi.unit && <span className="text-xs text-gray-400 ml-0.5">{kpi.unit}</span>}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-0.5">{kpi.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 퍼널 */}
                {funnel.length > 0 && (
                    <div>
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">전환 퍼널</h3>
                        <div className="space-y-2">
                            {funnel.map((stage, i) => {
                                const max = funnel[0]?.value || 1;
                                const pct = Math.round(stage.value / max * 100);
                                return (
                                    <div key={i} className="flex items-center gap-3">
                                        <div className="w-24 text-xs text-gray-500 text-right shrink-0">{stage.stage}</div>
                                        <div className="flex-1 h-6 bg-gray-100 rounded-lg overflow-hidden">
                                            <div
                                                className="h-full bg-indigo-500 rounded-lg flex items-center justify-end pr-2 transition-all"
                                                style={{ width: `${pct}%` }}
                                            >
                                                <span className="text-[10px] text-white font-bold">{stage.value.toLocaleString()}</span>
                                            </div>
                                        </div>
                                        <div className="w-10 text-xs text-gray-400 shrink-0">{pct}%</div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {kpis.length === 0 && funnel.length === 0 && (
                    <p className="text-sm text-gray-400 text-center py-4">리포트 데이터를 불러올 수 없습니다.</p>
                )}
            </div>
        </div>
    );
}
