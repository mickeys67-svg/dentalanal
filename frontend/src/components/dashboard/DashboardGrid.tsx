import React from 'react';
import { MarketShareChart } from '@/components/dashboard/MarketShareChart';
import { RankTable } from '@/components/dashboard/RankTable';
import { AIReport } from '@/components/dashboard/AIReport';
import { CompetitorData, SOVDataItem } from '@/types/mission';

interface DashboardGridProps {
    keyword: string;
    targetHospital: string;
    topN: number;
    sovData: { sov: number; total: number; hits: number; history?: SOVDataItem[] } | undefined;
    placeRankings: any[];
    viewRankings: any[];
    placeCompetitors: { competitors: CompetitorData[] } | undefined;
    viewCompetitors: { competitors: CompetitorData[] } | undefined;
}

export function DashboardGrid({
    keyword,
    targetHospital,
    topN,
    sovData,
    placeRankings,
    viewRankings,
    placeCompetitors,
    viewCompetitors
}: DashboardGridProps) {
    return (
        <div className="space-y-8">
            {/* SOV Summary */}
            {sovData && (
                <div className="bg-white p-6 rounded-2xl shadow-sm border">
                    <h2 className="text-xl font-bold mb-4">SOV (점유율) 분석</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                        <div className="p-4 bg-blue-50 rounded-xl">
                            <p className="text-sm text-gray-500 mb-1">총 검색 결과</p>
                            <p className="text-2xl font-bold text-blue-700">{sovData.total}개</p>
                        </div>
                        <div className="p-4 bg-blue-50 rounded-xl">
                            <p className="text-sm text-gray-500 mb-1">나의 병원 노출</p>
                            <p className="text-2xl font-bold text-blue-700">{sovData.hits}개</p>
                        </div>
                        <div className="p-4 bg-blue-50 rounded-xl">
                            <p className="text-sm text-gray-500 mb-1">SOV 점유율</p>
                            <p className="text-3xl font-bold text-indigo-600">{sovData.sov.toFixed(1)}%</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <MarketShareChart
                    title={`네이버 플레이스 점유율 (상위 ${topN})`}
                    data={placeCompetitors?.competitors || []}
                />
                <MarketShareChart
                    title={`네이버 뷰(블로그) 점유율 (상위 ${topN})`}
                    data={viewCompetitors?.competitors || []}
                />
            </div>

            {/* Rankings Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RankTable
                    title="네이버 플레이스 순위"
                    data={placeRankings || []}
                    targetHospital={targetHospital}
                    platform="NAVER_PLACE"
                />
                <RankTable
                    title="네이버 뷰(블로그) 순위"
                    data={viewRankings || []}
                    targetHospital={targetHospital}
                    platform="NAVER_VIEW"
                />
            </div>

            {/* AI Report Section */}
            <div className="mt-8">
                <AIReport
                    keyword={keyword}
                    targetHospital={targetHospital}
                    topN={topN}
                />
            </div>
        </div>
    );
}
