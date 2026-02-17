"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeywordRankTable } from "@/components/dashboard/KeywordRankTable";
import { CompetitorComparison } from "@/components/dashboard/CompetitorComparison";
import { KeywordSummary } from "@/components/dashboard/KeywordSummary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Loader2 } from "lucide-react";
import { scrapePlace, getRankings, getCompetitors } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { UI_TEXT } from "@/lib/i18n";

export default function PlaceRankPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [keyword, setKeyword] = useState("");
    const [searchedKeyword, setSearchedKeyword] = useState("");

    // Query for rankings
    const { data: rankings, isLoading: isRankingLoading } = useQuery({
        queryKey: ['rankings', searchedKeyword, 'NAVER_PLACE'],
        queryFn: () => getRankings(searchedKeyword, 'NAVER_PLACE'),
        enabled: !!searchedKeyword && searchedKeyword.length > 0,
        refetchOnWindowFocus: false,
    });

    // Query for competitors
    const { data: competitors, isLoading: isCompetitorLoading } = useQuery({
        queryKey: ['competitors', searchedKeyword, 'NAVER_PLACE'],
        queryFn: () => getCompetitors(searchedKeyword, 'NAVER_PLACE'),
        enabled: !!searchedKeyword && searchedKeyword.length > 0,
        refetchOnWindowFocus: false,
    });

    // Mutation for scraping
    const scrapeMutation = useMutation({
        mutationFn: (kw: string) => scrapePlace(kw, selectedClient?.id),
        onSuccess: () => {
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rankings', searchedKeyword] });
                queryClient.invalidateQueries({ queryKey: ['competitors', searchedKeyword] });
            }, 3500);
        },
        onError: (error) => {
            alert("조사에 실패했습니다. " + error);
        }
    });

    const handleSearch = () => {
        if (!keyword.trim()) return;
        setSearchedKeyword(keyword);
        scrapeMutation.mutate(keyword);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-10">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">{UI_TEXT.RANKING.TITLE}</h1>
                    <p className="text-muted-foreground mt-1">
                        {UI_TEXT.RANKING.SUBTITLE}
                    </p>
                </div>
            </div>

            {/* Search Section */}
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
            </div>

            {/* Summary Cards */}
            <KeywordSummary
                rankings={rankings}
                competitors={competitors}
                isLoading={isRankingLoading || isCompetitorLoading}
            />

            {/* Results Section */}
            <div className="grid gap-6">
                <KeywordRankTable
                    data={rankings || []}
                    isLoading={isRankingLoading || (scrapeMutation.isPending && !rankings)}
                    keyword={searchedKeyword}
                />

                <CompetitorComparison
                    data={competitors || null}
                    isLoading={isCompetitorLoading || (scrapeMutation.isPending && !competitors)}
                />
            </div>

            {/* Disclaimer */}
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-700">
                <div className="flex items-start gap-2">
                    <div className="font-bold shrink-0">{UI_TEXT.RANKING.INFO_TITLE}</div>
                    <div>
                        {UI_TEXT.RANKING.INFO_TEXT}
                    </div>
                </div>
            </div>
        </div>
    );
}
