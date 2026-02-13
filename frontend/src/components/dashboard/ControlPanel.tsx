import React from 'react';
import { AlertCircle, Target, Search, Settings } from 'lucide-react';
import { Client } from '@/types';

interface ControlPanelProps {
    selectedClient: Client | null;
    onOpenSetup: () => void;
    onScrapePlace: () => void;
    onScrapeView: () => void;
    isPlacePending: boolean;
    isViewPending: boolean;
}

export function ControlPanel({
    selectedClient,
    onOpenSetup,
    onScrapePlace,
    onScrapeView,
    isPlacePending,
    isViewPending,
}: ControlPanelProps) {
    if (!selectedClient) return null;

    return (
        <div className="bg-white/80 backdrop-blur-md p-6 rounded-3xl shadow-sm border border-gray-100 mb-8 flex flex-col md:flex-row items-center justify-between gap-6 transition-all">
            <div className="flex items-center gap-5">
                <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center text-primary">
                    <Target className="w-7 h-7" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedClient.name}</h2>
                    <p className="text-sm text-gray-500 font-medium">현재 활성화된 분석 프로젝트</p>
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                <button
                    onClick={onScrapePlace}
                    disabled={isPlacePending}
                    className="h-12 px-6 bg-white border border-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                    <Search className="w-4 h-4 text-green-500" />
                    {isPlacePending ? '수집 중...' : '플레이스 순위 수집'}
                </button>
                <button
                    onClick={onScrapeView}
                    disabled={isViewPending}
                    className="h-12 px-6 bg-white border border-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                    <Search className="w-4 h-4 text-emerald-500" />
                    {isViewPending ? '수집 중...' : 'VIEW(블로그) 수집'}
                </button>
                <button
                    onClick={onOpenSetup}
                    className="h-12 px-6 bg-primary text-white rounded-xl font-bold hover:shadow-lg hover:shadow-primary/20 transition-all flex items-center gap-2"
                >
                    <Settings className="w-4 h-4" />
                    조사 대상 및 키워드 설정
                </button>
            </div>
        </div>
    );
}
