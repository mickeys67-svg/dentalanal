'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getAIReport } from '@/lib/api';
import { Sparkles, Loader2, AlertCircle, RefreshCw } from 'lucide-react';

interface AIReportProps {
    keyword: string;
    targetHospital: string;
    topN: number;
}

export function AIReport({ keyword, targetHospital, topN }: AIReportProps) {
    const [report, setReport] = useState<string | null>(null);
    const [errorStatus, setErrorStatus] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: () => getAIReport(keyword, targetHospital, 'NAVER_PLACE', topN),
        onSuccess: (data: { report: string }) => {
            setReport(data.report);
            setErrorStatus(null);
        },
        onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
            setErrorStatus(error.response?.data?.detail || error.message || '리포트 생성 중 오류가 발생했습니다.');
            setReport(null);
        },
    });

    return (
        <div className="bg-card rounded-2xl border border-border shadow-card overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-primary rounded-lg shadow-sm">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h3 className="text-[15px] font-semibold text-foreground">AI 마케팅 데이터 분석 리포트</h3>
                        <p className="text-xs text-muted-foreground mt-0.5">AI 기반 심층 분석</p>
                    </div>
                </div>
                <button
                    onClick={() => mutation.mutate()}
                    disabled={mutation.isPending || !keyword || !targetHospital}
                    className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90
                               text-white px-4 py-2 rounded-xl text-sm font-semibold
                               shadow-sm transition-all
                               disabled:opacity-50 disabled:cursor-not-allowed
                               active:scale-[0.98]"
                >
                    {mutation.isPending ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                    )}
                    {mutation.isPending ? '생성 중...' : 'AI 분석 요청'}
                </button>
            </div>

            <div className="p-6">
                {/* Empty state */}
                {!report && !mutation.isPending && !errorStatus && (
                    <div className="border-2 border-dashed border-border rounded-xl p-10 text-center bg-background/50">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                            <Sparkles className="w-6 h-6 text-primary" />
                        </div>
                        <p className="text-muted-foreground font-medium text-sm">AI 마케팅 분석을 시작하세요</p>
                        <p className="text-xs text-muted-foreground mt-1">경쟁 브랜드 SOV와 내 브랜드 데이터를 비교 분석합니다.</p>
                    </div>
                )}

                {/* Loading skeleton */}
                {mutation.isPending && (
                    <div className="space-y-3 animate-pulse">
                        {[3, 5, 4, 6, 3].map((w, i) => (
                            <div key={i} className={`h-4 bg-secondary rounded-lg w-${w}/6`} />
                        ))}
                    </div>
                )}

                {/* Error */}
                {errorStatus && (
                    <div className="bg-red-50 border border-red-100 rounded-xl p-4 flex items-start gap-3">
                        <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="text-sm font-semibold text-red-700">분석 실패</p>
                            <p className="text-xs text-red-600 mt-0.5">{errorStatus}</p>
                            <p className="text-xs text-red-400 mt-2">
                                * GOOGLE_API_KEY가 .env 파일에 올바르게 설정되어 있는지 확인해주세요.
                            </p>
                            <button
                                onClick={() => mutation.mutate()}
                                className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-red-600 hover:text-red-700"
                            >
                                <RefreshCw className="w-3 h-3" /> 다시 시도
                            </button>
                        </div>
                    </div>
                )}

                {/* Report content */}
                {report && (
                    <div className="bg-primary/10 rounded-xl p-5 border border-primary">
                        <div className="whitespace-pre-wrap text-sm text-foreground leading-relaxed">
                            {report}
                        </div>
                        <div className="mt-5 pt-4 border-t border-primary flex items-center gap-1.5 text-xs text-primary">
                            <AlertCircle className="w-3.5 h-3.5" />
                            본 리포트는 AI에 의해 생성된 분석이며, 참고용으로 활용해 주세요.
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
