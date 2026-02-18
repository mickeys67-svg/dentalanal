"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeywordRankTable } from "@/components/dashboard/KeywordRankTable";
import { CompetitorComparison } from "@/components/dashboard/CompetitorComparison";
import { KeywordSummary } from "@/components/dashboard/KeywordSummary";
import KeywordPositioningMap from "@/components/dashboard/KeywordPositioningMap";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { scrapePlace, getRankings, getCompetitors } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { UI_TEXT } from "@/lib/i18n";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function PlaceRankPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [keyword, setKeyword] = useState("");
    const [searchedKeyword, setSearchedKeyword] = useState("");
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const { data: rankings, isLoading: isRankingLoading } = useQuery({
        queryKey: ['rankings', searchedKeyword, 'NAVER_PLACE'],
        queryFn: () => getRankings(searchedKeyword, 'NAVER_PLACE'),
        enabled: !!searchedKeyword,
        refetchOnWindowFocus: false,
    });

    const { data: competitors, isLoading: isCompetitorLoading } = useQuery({
        queryKey: ['competitors', searchedKeyword, 'NAVER_PLACE'],
        queryFn: () => getCompetitors(searchedKeyword, 'NAVER_PLACE'),
        enabled: !!searchedKeyword,
        refetchOnWindowFocus: false,
    });

    const scrapeMutation = useMutation({
        mutationFn: (kw: string) => scrapePlace(kw, selectedClient?.id),
        onSuccess: () => {
            setErrorMsg(null);
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rankings', searchedKeyword] });
                queryClient.invalidateQueries({ queryKey: ['competitors', searchedKeyword] });
            }, 3500);
        },
        onError: (error: unknown) => {
            const msg = error instanceof Error ? error.message : "조사 중 오류가 발생했습니다.";
            setErrorMsg(msg);
        }
    });

    const handleSearch = () => {
        if (!keyword.trim()) return;
        setErrorMsg(null);
        setSearchedKeyword(keyword);
        scrapeMutation.mutate(keyword);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-10">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">{UI_TEXT.RANKING.TITLE}</h1>
                    <p className="text-muted-foreground mt-1">{UI_TEXT.RANKING.SUBTITLE}</p>
                </div>
            </div>

            {/* Search */}
            <div className="bg-white p-6 rounded-xl border shadow-sm">
                <label className="text-sm font-medium text-gray-700 mb-2 block">{UI_TEXT.RANKING.SEARCH_LABEL}</label>
                <div className="flex gap-3 max-w-lg">
                    <Input
                        placeholder={UI_TEXT.RANKING.SEARCH_PLACEHOLDER}
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="bg-white"
                    />
                    <Button
                        onClick={handleSearch}
                        disabled={scrapeMutation.isPending || !keyword.trim()}
                        className="w-24 bg-blue-600 hover:bg-blue-700"
                    >
                        {scrapeMutation.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <>
                                <Search className="w-4 h-4 mr-2" />
                                {UI_TEXT.RANKING.BUTTON_SEARCH}
                            </>
                        )}
                    </Button>
                </div>

                {errorMsg && (
                    <Alert variant="destructive" className="mt-3 max-w-lg">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription className="flex items-center justify-between">
                            <span>{errorMsg}</span>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-auto p-1 text-destructive hover:text-destructive"
                                onClick={handleSearch}
                            >
                                <RefreshCw className="w-3 h-3 mr-1" />
                                재시도
                            </Button>
                        </AlertDescription>
                    </Alert>
                )}
            </div>

            {/* Summary Cards */}
            <ErrorBoundary>
                <KeywordSummary
                    rankings={rankings}
                    competitors={competitors}
                    isLoading={isRankingLoading || isCompetitorLoading}
                />
            </ErrorBoundary>

            {/* Results */}
            <div className="grid gap-6">
                <ErrorBoundary>
                    <KeywordRankTable
                        data={rankings || []}
                        isLoading={isRankingLoading || (scrapeMutation.isPending && !rankings)}
                        keyword={searchedKeyword}
                    />
                </ErrorBoundary>

                <ErrorBoundary>
                    <CompetitorComparison
                        data={competitors || null}
                        isLoading={isCompetitorLoading || (scrapeMutation.isPending && !competitors)}
                    />
                </ErrorBoundary>
            </div>

            {/* Keyword Positioning Map — 클라이언트 선택 시에만 표시 */}
            {selectedClient && (
                <ErrorBoundary>
                    <KeywordPositioningMap
                        clientId={selectedClient.id}
                        platform="NAVER_PLACE"
                        days={30}
                    />
                </ErrorBoundary>
            )}

            {/* Disclaimer */}
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-700">
                <div className="flex items-start gap-2">
                    <div className="font-bold shrink-0">{UI_TEXT.RANKING.INFO_TITLE}</div>
                    <div>{UI_TEXT.RANKING.INFO_TEXT}</div>
                </div>
            </div>
        </div>
    );
}
