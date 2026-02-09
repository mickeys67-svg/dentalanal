'use client';

import { useMission } from '@/hooks/useMission';
import { ControlPanel } from '@/components/dashboard/ControlPanel';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';

export default function Home() {
  const {
    keyword, setKeyword,
    targetHospital, setTargetHospital,
    topN, setTopN,
    placeMutation,
    viewMutation,
    sovData,
    placeRankings,
    viewRankings,
    placeCompetitors,
    viewCompetitors,
    handleRefresh
  } = useMission();

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-2">
              D-MIND <span className="text-blue-600">INSIGHT</span>
            </h1>
            <p className="text-gray-500">
              치과 마케팅 성과 분석 및 경쟁사 리포트
            </p>
          </div>
          <div className="text-right hidden md:block">
            <p className="text-sm text-gray-400">Analysis Engine v1.0</p>
            <p className="text-xs text-gray-300">Powered by Gemini AI</p>
          </div>
        </div>

        {/* Control Panel */}
        <ControlPanel
          keyword={keyword}
          setKeyword={setKeyword}
          targetHospital={targetHospital}
          setTargetHospital={setTargetHospital}
          topN={topN}
          setTopN={setTopN}
          onScrapePlace={() => placeMutation.mutate(keyword)}
          onScrapeView={() => viewMutation.mutate(keyword)}
          onRefresh={handleRefresh}
          isPlacePending={placeMutation.isPending}
          isViewPending={viewMutation.isPending}
        />

        {/* Dashboard Grid */}
        <DashboardGrid
          keyword={keyword}
          targetHospital={targetHospital}
          topN={topN}
          sovData={sovData}
          placeRankings={placeRankings}
          viewRankings={viewRankings}
          placeCompetitors={placeCompetitors}
          viewCompetitors={viewCompetitors}
        />
      </div>
    </main>
  );
}
