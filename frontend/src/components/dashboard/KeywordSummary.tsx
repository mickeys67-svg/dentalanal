"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KeywordRank, CompetitorAnalysisResult } from "@/types";
import { Trophy, TrendingUp, Hash, Users } from "lucide-react";

interface KeywordSummaryProps {
    rankings: KeywordRank[] | undefined;
    competitors: CompetitorAnalysisResult | undefined;
    isLoading: boolean;
}

export function KeywordSummary({ rankings, competitors, isLoading }: KeywordSummaryProps) {
    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-24 rounded-xl bg-gray-100 animate-pulse" />
                ))}
            </div>
        );
    }

    if (!rankings || rankings.length === 0) return null;

    // Calculate Metrics
    const totalKeywords = rankings.length;
    const top3Count = rankings.filter(r => r.rank <= 3).length;
    const avgRank = rankings.reduce((acc, curr) => acc + curr.rank, 0) / totalKeywords;

    // Competitor Dominance (Most frequent #1 competitor)
    // Assuming competitors data has this info, otherwise use a placeholder or derive from rankings if competitor info was embedded (it's not).
    // actually competitors.competitors[0] is usually the top one.
    const topCompetitor = competitors?.competitors?.[0];

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">상위 노출 (Top 3)</CardTitle>
                    <Trophy className="h-4 w-4 text-amber-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{top3Count} <span className="text-xs text-muted-foreground font-normal">/ {totalKeywords}</span></div>
                    <p className="text-xs text-muted-foreground">
                        전체 키워드 중 {((top3Count / totalKeywords) * 100).toFixed(0)}%
                    </p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">평균 순위</CardTitle>
                    <TrendingUp className="h-4 w-4 text-blue-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{avgRank.toFixed(1)} <span className="text-xs text-muted-foreground font-normal">위</span></div>
                    <p className="text-xs text-muted-foreground">
                        전체 키워드 평균
                    </p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">추적 키워드</CardTitle>
                    <Hash className="h-4 w-4 text-gray-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{totalKeywords} <span className="text-xs text-muted-foreground font-normal">개</span></div>
                    <p className="text-xs text-muted-foreground">
                        등록된 키워드 수
                    </p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">경쟁 강도</CardTitle>
                    <Users className="h-4 w-4 text-purple-500" />
                </CardHeader>
                <CardContent>
                    {topCompetitor ? (
                        <>
                            <div className="text-lg font-bold truncate" title={topCompetitor.name}>{topCompetitor.name}</div>
                            <p className="text-xs text-muted-foreground">
                                1위 경쟁사 (점유율 {topCompetitor.share.toFixed(0)}%)
                            </p>
                        </>
                    ) : (
                        <div className="text-sm text-muted-foreground">데이터 분석 중</div>
                    )}

                </CardContent>
            </Card>
        </div>
    );
}
