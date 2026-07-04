"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MentionFeed } from "@/components/dashboard/MentionFeed";
import { SentimentGauge } from "@/components/dashboard/SentimentGauge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, Loader2, AlertCircle, RefreshCw, TrendingUp } from "lucide-react";
import { scrapeView, getRankings, getRankingTrend } from "@/lib/api";
import { useClient } from "@/components/providers/ClientProvider";
import { UI_TEXT } from "@/lib/i18n";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { CompetitorDiscovery } from "@/components/dashboard/CompetitorDiscovery";
import { TrendAlerts } from "@/components/dashboard/TrendAlerts";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

export default function ViralPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [keyword, setKeyword] = useState("");
    const [searchedKeyword, setSearchedKeyword] = useState("");
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const { data: viralPosts, isLoading: isPostsLoading } = useQuery({
        queryKey: ['rankings', searchedKeyword, 'NAVER_VIEW'],
        queryFn: () => getRankings(searchedKeyword, 'NAVER_VIEW'),
        enabled: !!searchedKeyword,
        refetchOnWindowFocus: false,
    });

    const { data: trendData, isLoading: isTrendLoading } = useQuery({
        queryKey: ['rankingTrend', searchedKeyword, 'NAVER_VIEW'],
        queryFn: () => getRankingTrend({
            keyword: searchedKeyword,
            target_hospital: selectedClient?.name || '',
            platform: 'NAVER_VIEW',
            days: 14,
        }),
        enabled: !!searchedKeyword && !!selectedClient,
        refetchOnWindowFocus: false,
    });

    const scrapeMutation = useMutation({
        mutationFn: (kw: string) => scrapeView(kw, selectedClient?.id),
        onSuccess: () => {
            setErrorMsg(null);
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rankings', searchedKeyword, 'NAVER_VIEW'] });
                queryClient.invalidateQueries({ queryKey: ['rankingTrend', searchedKeyword, 'NAVER_VIEW'] });
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
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">{UI_TEXT.VIRAL.TITLE}</h1>
                    <p className="text-muted-foreground mt-1">{UI_TEXT.VIRAL.SUBTITLE}</p>
                </div>
            </div>

            {/* Search */}
            <div className="bg-card p-6 rounded-xl border shadow-sm">
                <label className="text-sm font-medium text-foreground mb-2 block">{UI_TEXT.VIRAL.SEARCH_LABEL}</label>
                <div className="flex gap-3 max-w-lg">
                    <Input
                        placeholder={UI_TEXT.VIRAL.SEARCH_PLACEHOLDER}
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="bg-card"
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

            {/* Trend Chart — 클라이언트 선택 + 키워드 검색 시 표시 */}
            {selectedClient && searchedKeyword && (
                <ErrorBoundary>
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg font-bold flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-blue-500" />
                                블로그 순위 트렌드 (최근 14일)
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {isTrendLoading ? (
                                <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                                    <Loader2 className="w-6 h-6 animate-spin mr-2" />
                                    <span className="text-sm">트렌드 로딩 중...</span>
                                </div>
                            ) : trendData && trendData.length > 0 ? (
                                <div className="h-[200px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 11 }}
                                                tickFormatter={(v) => v.slice(5)}
                                            />
                                            <YAxis
                                                reversed
                                                domain={[1, 'auto']}
                                                tick={{ fontSize: 11 }}
                                                tickFormatter={(v) => `${v}위`}
                                            />
                                            <Tooltip
                                                contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                                                formatter={(v: number | undefined) => v !== undefined ? [`${v}위`, '순위'] : ['-', '순위']}
                                                labelFormatter={(l) => `날짜: ${l}`}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="rank"
                                                stroke="#3b82f6"
                                                strokeWidth={2}
                                                dot={{ r: 3 }}
                                                activeDot={{ r: 5 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
                                    트렌드 데이터가 없습니다. 키워드를 검색하면 이후 데이터가 수집됩니다.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </ErrorBoundary>
            )}

            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2">
                    <ErrorBoundary>
                        <MentionFeed
                            data={viralPosts || []}
                            isLoading={isPostsLoading || (scrapeMutation.isPending && !viralPosts)}
                        />
                    </ErrorBoundary>
                </div>

                <div className="md:col-span-1 space-y-6">
                    <ErrorBoundary>
                        <SentimentGauge
                            isLoading={isPostsLoading || (scrapeMutation.isPending && !viralPosts)}
                        />
                    </ErrorBoundary>

                    {viralPosts && viralPosts.length > 0 && (
                        <Card className="p-4 bg-blue-50 border-blue-100">
                            <h4 className="font-semibold text-blue-900 text-sm mb-1">💡 Insight</h4>
                            <p className="text-xs text-blue-700 leading-relaxed">
                                총 <strong>{viralPosts.length}개</strong> 포스트가 수집되었습니다.
                                상위 노출 콘텐츠를 분석해 마케팅 전략에 활용하세요.
                            </p>
                        </Card>
                    )}
                </div>
            </div>

            {/* 경쟁사 발굴 + 트렌드 알림 — 클라이언트 선택 시에만 표시 */}
            {selectedClient && (
                <>
                    <ErrorBoundary>
                        <CompetitorDiscovery
                            clientId={selectedClient.id}
                            platform="NAVER_VIEW"
                        />
                    </ErrorBoundary>

                    <ErrorBoundary>
                        <TrendAlerts clientId={selectedClient.id} />
                    </ErrorBoundary>
                </>
            )}
        </div>
    );
}
