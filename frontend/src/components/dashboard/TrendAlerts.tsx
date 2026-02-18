"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
    Bell,
    AlertTriangle,
    TrendingDown,
    TrendingUp,
    Minus,
    Loader2,
    RefreshCw,
    AlertCircle,
} from "lucide-react";
import { createRankingDropAlert, predictSearchTrends, RankingDropAlert } from "@/lib/api";

interface TrendAlertsProps {
    clientId: string;
}

function DropAlertItem({ item }: { item: RankingDropAlert }) {
    const severity = item.drop >= 10 ? "high" : item.drop >= 5 ? "medium" : "low";
    const colors = {
        high: "border-red-300 bg-red-50 text-red-700",
        medium: "border-orange-300 bg-orange-50 text-orange-700",
        low: "border-yellow-300 bg-yellow-50 text-yellow-700",
    };
    return (
        <div className={`flex items-center justify-between p-3 rounded-lg border ${colors[severity]}`}>
            <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 shrink-0" />
                <span className="font-medium text-sm">{item.keyword}</span>
            </div>
            <div className="flex items-center gap-3 text-xs">
                <span className="tabular-nums">{item.previous_rank}위 → {item.current_rank}위</span>
                <Badge
                    variant="outline"
                    className={`${colors[severity]} border-current text-[10px]`}
                >
                    -{item.drop}위
                </Badge>
            </div>
        </div>
    );
}

function PredictionBadge({ prediction }: { prediction: string }) {
    if (prediction.includes("상승")) return (
        <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
            <TrendingUp className="w-3 h-3" /> {prediction}
        </span>
    );
    if (prediction.includes("하락")) return (
        <span className="flex items-center gap-1 text-red-500 text-xs font-medium">
            <TrendingDown className="w-3 h-3" /> {prediction}
        </span>
    );
    return (
        <span className="flex items-center gap-1 text-gray-500 text-xs font-medium">
            <Minus className="w-3 h-3" /> {prediction}
        </span>
    );
}

export function TrendAlerts({ clientId }: TrendAlertsProps) {
    const [drops, setDrops] = useState<RankingDropAlert[] | null>(null);
    const [dropError, setDropError] = useState<string | null>(null);

    // 순위 급락 알림 생성 뮤테이션
    const dropMutation = useMutation({
        mutationFn: () => createRankingDropAlert(clientId, 5),
        onSuccess: (data) => {
            setDrops(data.drops);
            setDropError(null);
        },
        onError: (err: unknown) => {
            setDropError(err instanceof Error ? err.message : "분석에 실패했습니다.");
        },
    });

    // 검색 트렌드 예측 쿼리
    const {
        data: trendResult,
        isLoading: isTrendLoading,
        error: trendError,
        refetch: refetchTrend,
    } = useQuery({
        queryKey: ["searchTrends", clientId],
        queryFn: () => predictSearchTrends(clientId, 90),
        enabled: !!clientId,
        refetchOnWindowFocus: false,
        retry: 1,
    });

    const trendData = trendResult?.data;
    const trendEntries = trendData
        ? Object.entries(trendData.predictions).slice(0, 6)
        : [];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 순위 급락 알림 */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Bell className="w-5 h-5 text-orange-500" />
                        순위 급락 감지
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                        전일 대비 5위 이상 하락한 키워드를 감지합니다.
                    </p>
                </CardHeader>
                <CardContent className="space-y-4">
                    {dropError && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>{dropError}</AlertDescription>
                        </Alert>
                    )}

                    <Button
                        onClick={() => dropMutation.mutate()}
                        disabled={dropMutation.isPending}
                        variant="outline"
                        className="w-full border-orange-300 text-orange-700 hover:bg-orange-50"
                    >
                        {dropMutation.isPending ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                분석 중...
                            </>
                        ) : (
                            <>
                                <AlertTriangle className="w-4 h-4 mr-2" />
                                순위 급락 체크
                            </>
                        )}
                    </Button>

                    {dropMutation.isPending && (
                        <div className="space-y-2">
                            {[...Array(3)].map((_, i) => (
                                <Skeleton key={i} className="h-12 w-full rounded-lg" />
                            ))}
                        </div>
                    )}

                    {drops && !dropMutation.isPending && (
                        <>
                            {drops.length === 0 ? (
                                <div className="flex flex-col items-center gap-2 py-6 text-center">
                                    <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                                        <TrendingUp className="w-5 h-5 text-green-600" />
                                    </div>
                                    <p className="text-sm font-medium text-green-700">순위 급락 없음</p>
                                    <p className="text-xs text-muted-foreground">모든 키워드가 안정적입니다.</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <p className="text-xs text-muted-foreground">
                                        {drops.length}개 키워드에서 급락 감지
                                    </p>
                                    {drops.map((d) => (
                                        <DropAlertItem key={d.keyword_id} item={d} />
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {!drops && !dropMutation.isPending && (
                        <div className="text-center py-4 text-xs text-muted-foreground border rounded-lg bg-gray-50">
                            버튼을 클릭해 순위 변화를 확인하세요.
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* 검색 트렌드 예측 */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-blue-500" />
                            키워드 트렌드 예측
                        </CardTitle>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => refetchTrend()}
                            disabled={isTrendLoading}
                            className="h-7 px-2"
                        >
                            <RefreshCw className={`w-3 h-3 ${isTrendLoading ? "animate-spin" : ""}`} />
                        </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                        SMA 기반 순위 상승/하락 추세를 예측합니다.
                    </p>
                </CardHeader>
                <CardContent>
                    {isTrendLoading && (
                        <div className="space-y-3">
                            {[...Array(4)].map((_, i) => (
                                <Skeleton key={i} className="h-10 w-full rounded-lg" />
                            ))}
                        </div>
                    )}

                    {trendError && !isTrendLoading && (
                        <div className="text-center py-6 text-sm text-muted-foreground">
                            트렌드 데이터를 불러오지 못했습니다.
                            <br />키워드 데이터가 충분히 쌓이면 자동으로 표시됩니다.
                        </div>
                    )}

                    {trendData && !isTrendLoading && (
                        <>
                            {trendEntries.length === 0 ? (
                                <div className="text-center py-6 text-sm text-muted-foreground">
                                    예측할 키워드 데이터가 없습니다.
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <p className="text-xs text-muted-foreground">
                                        분석 기간: {trendData.analysis_period}
                                    </p>
                                    {trendEntries.map(([keyword, pred]) => (
                                        <div
                                            key={keyword}
                                            className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border"
                                        >
                                            <span className="font-medium text-sm truncate mr-2">{keyword}</span>
                                            <div className="flex items-center gap-3 shrink-0 text-xs text-muted-foreground">
                                                <span>평균 {pred.recent_avg.toFixed(1)}위</span>
                                                <PredictionBadge prediction={pred.prediction} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
