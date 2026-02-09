'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getAIReport } from '@/lib/api';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';

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
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onSuccess: (data: any) => {
            setReport(data.report);
            setErrorStatus(null);
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onError: (error: any) => {
            setErrorStatus(error.response?.data?.detail || error.message || '리포트 생성 중 오류가 발생했습니다.');
            setReport(null);
        }
    });

    return (
        <div className="bg-white p-6 rounded-lg shadow mt-8">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-purple-600" />
                    <h3 className="text-xl font-bold text-gray-900">AI 마케팅 성과 분석 리포트</h3>
                </div>
                <button
                    onClick={() => mutation.mutate()}
                    disabled={mutation.isPending || !keyword || !targetHospital}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {mutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Sparkles className="w-4 h-4" />
                    )}
                    {mutation.isPending ? '리포트 생성 중...' : 'AI 분석 요청'}
                </button>
            </div>

            {!report && !mutation.isPending && (
                <div className="bg-gray-50 border-2 border-dashed rounded-xl p-12 text-center">
                    <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 font-medium">현재 데이터를 기반으로 AI 마케팅 제언을 받아보세요.</p>
                    <p className="text-sm text-gray-400 mt-2">상위 노출된 경쟁사와 나의 SOV를 비교 분석합니다.</p>
                </div>
            )}

            {mutation.isPending && (
                <div className="space-y-4 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                    <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-4/5"></div>
                </div>
            )}

            {errorStatus && (
                <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-red-700 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 mt-0.5" />
                    <div>
                        <p className="font-bold">분석 실패</p>
                        <p className="text-sm">{errorStatus}</p>
                        <p className="text-xs mt-2 text-red-500">* Google Gemini API 키가 .env 파일에 GOOGLE_API_KEY로 올바르게 설정되어 있는지 확인해주세요.</p>
                    </div>
                </div>
            )}

            {report && (
                <div className="bg-purple-50 rounded-xl p-6 border border-purple-100 prose prose-purple max-w-none">
                    <div className="whitespace-pre-wrap text-gray-800 leading-relaxed font-sans">
                        {report}
                    </div>
                    <div className="mt-8 pt-4 border-t border-purple-200 text-xs text-purple-400 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        본 리포트는 인공지능에 의해 생성된 마켓 분석이며, 참고용으로 활용해 주세요.
                    </div>
                </div>
            )}
        </div>
    );
}
