"use client";

import { useClient } from "../providers/ClientProvider";
import { BarChart3, Search } from "lucide-react";

interface DashboardEmptyStateProps {
    onSync: () => void;
    isSyncing: boolean;
}

export function DashboardEmptyState({ onSync, isSyncing }: DashboardEmptyStateProps) {
    const { selectedClient } = useClient();

    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] border-2 border-dashed border-gray-200 rounded-3xl p-8 bg-gray-50/50">
            <div className="bg-white p-4 rounded-full shadow-sm mb-4">
                <Search className="w-8 h-8 text-primary" />
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-2">
                아직 분석된 데이터가 없습니다
            </h2>

            <p className="text-gray-500 text-center max-w-md mb-8">
                {selectedClient
                    ? `현재 '${selectedClient.name}' 프로젝트의 광고 성과 데이터가 비어있습니다. 실시간 조사를 시작하여 데이터를 불러오세요.`
                    : "먼저 분석할 프로젝트(치과)를 선택해주세요."}
            </p>

            {selectedClient && (
                <button
                    onClick={onSync}
                    disabled={isSyncing}
                    className="flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-3 rounded-xl font-bold transition-all shadow-lg hover:shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSyncing ? (
                        <>
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/20 border-t-white mr-2" />
                            데이터 분석 중...
                        </>
                    ) : (
                        <>
                            <BarChart3 className="w-5 h-5" />
                            실시간 조사 시작
                        </>
                    )}
                </button>
            )}
        </div>
    );
}
