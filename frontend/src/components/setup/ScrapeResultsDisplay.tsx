import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface ScrapeResult {
    rank: number;
    rank_change?: number;
    target_name: string;
    target_type?: string;
    link?: string;
    captured_at: string;
}

interface ScrapeResultsDisplayProps {
    scrapeResults: {
        has_data: boolean;
        keyword: string;
        platform: string;
        results: ScrapeResult[];
        total_count: number;
    } | null;
    onContinue: () => void;
    onRetry: () => void;
    isLoading?: boolean;
}

export function ScrapeResultsDisplay({
    scrapeResults,
    onContinue,
    onRetry,
    isLoading = false
}: ScrapeResultsDisplayProps) {
    if (!scrapeResults) {
        return null;
    }

    return (
        <div className="mt-12 pt-8 border-t border-gray-50 animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
            <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">조사 결과</h3>
                <p className="text-gray-500">
                    키워드: {scrapeResults.keyword} | 매체: {
                        scrapeResults.platform === 'NAVER_PLACE' ? '네이버 플레이스' :
                        scrapeResults.platform === 'NAVER_VIEW' ? '네이버 VIEW' :
                        scrapeResults.platform
                    }
                </p>
            </div>

            {scrapeResults.has_data && scrapeResults.results.length > 0 ? (
                <>
                    <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                            <h4 className="text-lg font-bold text-green-900">
                                조사 완료! {scrapeResults.total_count}개의 결과를 찾았습니다.
                            </h4>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-green-200">
                                        <th className="text-left py-3 px-4 font-bold text-green-900">순위</th>
                                        <th className="text-left py-3 px-4 font-bold text-green-900">대상 (Target)</th>
                                        <th className="text-left py-3 px-4 font-bold text-green-900">유형</th>
                                        <th className="text-left py-3 px-4 font-bold text-green-900">수집 시간</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {scrapeResults.results.slice(0, 5).map((result, idx) => (
                                        <tr key={idx} className="border-b border-green-100 hover:bg-green-50/50 transition-colors">
                                            <td className="py-3 px-4 font-bold text-green-700">{result.rank}위</td>
                                            <td className="py-3 px-4 text-gray-800 font-medium">{result.target_name}</td>
                                            <td className="py-3 px-4 text-gray-600 text-xs">{result.target_type || '-'}</td>
                                            <td className="py-3 px-4 text-gray-500 text-xs">
                                                {new Date(result.captured_at).toLocaleString('ko-KR')}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {scrapeResults.total_count > 5 && (
                            <p className="text-xs text-gray-600 mt-4 font-medium">
                                ... 외 {scrapeResults.total_count - 5}개 결과 (대시보드에서 전체 확인 가능)
                            </p>
                        )}
                    </div>

                    <button
                        onClick={onContinue}
                        disabled={isLoading}
                        className="w-full h-14 bg-primary text-white font-bold rounded-2xl shadow-lg shadow-primary/30 hover:shadow-primary/40 active:scale-95 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                    >
                        <CheckCircle2 className="w-5 h-5" /> 대시보드로 이동
                    </button>
                </>
            ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-1" />
                        <div className="flex-1">
                            <h4 className="text-lg font-bold text-amber-900 mb-3">아직 데이터를 수집 중입니다</h4>
                            <p className="text-amber-800 text-sm mb-4">
                                조사가 진행 중이거나 해당 키워드로 저장된 데이터가 없습니다.
                                <br />
                                잠시 후 다시 확인해주세요. (일반적으로 1-2분 소요)
                            </p>
                            <button
                                onClick={onRetry}
                                disabled={isLoading}
                                className="px-4 py-2 bg-white border border-amber-300 text-amber-900 font-semibold rounded-lg hover:bg-amber-50 transition-colors text-sm disabled:opacity-50"
                            >
                                다시 확인
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
