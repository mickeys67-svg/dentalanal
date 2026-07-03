"use client";

import { useClient } from "../providers/ClientProvider";
import { BarChart3, Sparkles, ArrowRight } from "lucide-react";

interface DashboardEmptyStateProps {
    onSync: () => void;
    isSyncing: boolean;
}

export function DashboardEmptyState({ onSync, isSyncing }: DashboardEmptyStateProps) {
    const { selectedClient } = useClient();

    return (
        <div className="flex flex-col items-center justify-center min-h-[420px] rounded-2xl border-2 border-dashed border-slate-200 p-10 bg-slate-50/40">
            {/* Icon */}
            <div className="relative mb-6">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-200">
                    <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-amber-400 flex items-center justify-center">
                    <Sparkles className="w-3 h-3 text-white" />
                </div>
            </div>

            <h2 className="text-xl font-bold text-slate-900 mb-2 text-center">
                {selectedClient ? "아직 분석된 데이터가 없습니다" : "프로젝트를 선택해주세요"}
            </h2>

            <p className="text-slate-500 text-center max-w-sm text-sm leading-relaxed mb-8">
                {selectedClient
                    ? `'${selectedClient.name}' 프로젝트의 광고 성과 데이터가 비어있습니다. 실시간 조사를 시작하여 마케팅 인사이트를 확인해보세요.`
                    : "상단 헤더에서 분석할 치과 프로젝트를 선택하면 성과 데이터와 AI 인사이트가 표시됩니다."}
            </p>

            {selectedClient && (
                <button
                    onClick={onSync}
                    disabled={isSyncing}
                    className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700
                               text-white px-6 py-3 rounded-xl font-semibold text-sm
                               shadow-lg shadow-indigo-200 hover:shadow-indigo-300
                               transition-all duration-200 active:scale-[0.98]
                               disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
                >
                    {isSyncing ? (
                        <>
                            <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            데이터 분석 중...
                        </>
                    ) : (
                        <>
                            <BarChart3 className="w-4 h-4" />
                            실시간 조사 시작
                            <ArrowRight className="w-4 h-4" />
                        </>
                    )}
                </button>
            )}
        </div>
    );
}
