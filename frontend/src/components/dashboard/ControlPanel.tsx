import React from 'react';

interface ControlPanelProps {
    keyword: string;
    setKeyword: (value: string) => void;
    targetHospital: string;
    setTargetHospital: (value: string) => void;
    topN: number;
    setTopN: (value: number) => void;
    onScrapePlace: () => void;
    onScrapeView: () => void;
    onRefresh: () => void;
    isPlacePending: boolean;
    isViewPending: boolean;
}

export function ControlPanel({
    keyword, setKeyword,
    targetHospital, setTargetHospital,
    topN, setTopN,
    onScrapePlace,
    onScrapeView,
    onRefresh,
    isPlacePending,
    isViewPending
}: ControlPanelProps) {
    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border mb-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">분석 키워드</label>
                    <input
                        type="text"
                        title="검색 키워드"
                        placeholder="예: 송도 치과"
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        className="w-full border p-2 rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">대상 병원 (나의 병원)</label>
                    <input
                        type="text"
                        title="분석 대상 병원명"
                        placeholder="예: 기록하는 습관"
                        value={targetHospital}
                        onChange={(e) => setTargetHospital(e.target.value)}
                        className="w-full border p-2 rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">분석 범위 선택</label>
                    <select
                        title="분석할 상위 순위 범위"
                        value={topN}
                        onChange={(e) => setTopN(Number(e.target.value))}
                        className="w-full border p-2 rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                        <option value={5}>상위 5위</option>
                        <option value={10}>상위 10위</option>
                        <option value={20}>상위 20위</option>
                    </select>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={onScrapePlace}
                        disabled={isPlacePending}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50 transition-all flex-1"
                    >
                        {isPlacePending ? '수집 중...' : '플레이스 수집'}
                    </button>
                    <button
                        onClick={onScrapeView}
                        disabled={isViewPending}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50 transition-all flex-1"
                    >
                        {isViewPending ? '수집 중...' : '블로그 수집'}
                    </button>
                    <button
                        onClick={onRefresh}
                        className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-lg font-medium transition-all"
                    >
                        새로고침
                    </button>
                </div>
            </div>
        </div>
    );
}
