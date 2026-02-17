"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MentionFeed } from "@/components/dashboard/MentionFeed";
import { SentimentGauge } from "@/components/dashboard/SentimentGauge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Loader2 } from "lucide-react";
import { scrapeView, getRankings } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { UI_TEXT } from "@/lib/i18n";
import { Card } from "@/components/ui/card";

export default function ViralPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [keyword, setKeyword] = useState("");
    const [searchedKeyword, setSearchedKeyword] = useState("");

    // Query for viral posts (using rankings API with NAVER_VIEW platform)
    const { data: viralPosts, isLoading: isPostsLoading } = useQuery({
        queryKey: ['rankings', searchedKeyword, 'NAVER_VIEW'],
        queryFn: () => getRankings(searchedKeyword, 'NAVER_VIEW'),
        enabled: !!searchedKeyword && searchedKeyword.length > 0,
        refetchOnWindowFocus: false,
    });

    // Mutation for scraping views
    const scrapeMutation = useMutation({
        mutationFn: (kw: string) => scrapeView(kw, selectedClient?.id),
        onSuccess: () => {
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rankings', searchedKeyword, 'NAVER_VIEW'] });
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
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">{UI_TEXT.VIRAL.TITLE}</h1>
                    <p className="text-muted-foreground mt-1">
                        {UI_TEXT.VIRAL.SUBTITLE}
                    </p>
                </div>
            </div>

            {/* Search Section */}
            <div className="bg-white p-6 rounded-xl border shadow-sm">
                <label className="text-sm font-medium text-gray-700 mb-2 block">{UI_TEXT.VIRAL.SEARCH_LABEL}</label>
                <div className="flex gap-3 max-w-lg">
                    <Input
                        placeholder={UI_TEXT.VIRAL.SEARCH_PLACEHOLDER}
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

            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Left: Feed (2 cols) */}
                <div className="md:col-span-2">
                    <MentionFeed
                        data={viralPosts || []}
                        isLoading={isPostsLoading || (scrapeMutation.isPending && !viralPosts)}
                    />
                </div>

                {/* Right: Sentiment (1 col) */}
                <div className="md:col-span-1">
                    <SentimentGauge
                        isLoading={isPostsLoading || (scrapeMutation.isPending && !viralPosts)}
                    />

                    {/* Placeholder for future expansion */}
                    <Card className="mt-6 p-4 bg-blue-50 border-blue-100 hidden md:block">
                        <h4 className="font-semibold text-blue-900 text-sm mb-1">💡 Insight</h4>
                        <p className="text-xs text-blue-700 leading-relaxed">
                            긍정적인 후기가 65%로 우세합니다. 최근 "원장님 친절함" 키워드가 블로그에서 자주 언급되고 있습니다.
                        </p>
                    </Card>
                </div>
            </div>
        </div>
    );
}
