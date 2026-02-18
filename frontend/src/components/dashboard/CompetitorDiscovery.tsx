"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
    Search,
    Loader2,
    AlertCircle,
    Users,
    TrendingUp,
    Tag,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import { discoverCompetitors, CompetitorDiscoveryItem } from "@/lib/api";

interface CompetitorDiscoveryProps {
    clientId: string;
    platform?: "NAVER_PLACE" | "NAVER_VIEW";
}

const PLATFORM_LABELS = {
    NAVER_PLACE: "네이버 플레이스",
    NAVER_VIEW: "네이버 블로그",
};

function ScoreBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const color =
        pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-orange-400" : "bg-yellow-400";
    return (
        <div className="flex items-center gap-2 w-full">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs font-semibold tabular-nums w-8 text-right">{pct}%</span>
        </div>
    );
}

function CompetitorCard({ item, rank }: { item: CompetitorDiscoveryItem; rank: number }) {
    const [expanded, setExpanded] = useState(false);
    const pct = Math.round(item.overlap_score * 100);
    const danger = pct >= 70;

    return (
        <div
            className={`border rounded-lg p-4 transition-colors ${
                danger ? "border-red-200 bg-red-50/30" : "border-gray-200 bg-white"
            }`}
        >
            <div className="flex items-start gap-3">
                {/* 순위 뱃지 */}
                <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${
                        rank <= 3 ? "bg-red-500" : rank <= 6 ? "bg-orange-400" : "bg-gray-400"
                    }`}
                >
                    {rank}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="font-semibold text-sm truncate">{item.name}</span>
                        {danger && (
                            <Badge variant="outline" className="text-red-600 border-red-300 text-[10px] shrink-0">
                                주요 경쟁사
                            </Badge>
                        )}
                    </div>

                    <ScoreBar score={item.overlap_score} />

                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            공유 키워드 {item.shared_keywords}개
                        </span>
                        <span className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" />
                            {item.keywords_appeared}회 노출
                        </span>
                    </div>

                    {/* 공유 키워드 펼치기 */}
                    {item.shared_keyword_terms.length > 0 && (
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="mt-2 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            공유 키워드 보기
                        </button>
                    )}

                    {expanded && (
                        <div className="mt-2 flex flex-wrap gap-1">
                            {item.shared_keyword_terms.map((kw) => (
                                <span
                                    key={kw}
                                    className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[11px]"
                                >
                                    {kw}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export function CompetitorDiscovery({ clientId, platform = "NAVER_PLACE" }: CompetitorDiscoveryProps) {
    const [activePlatform, setActivePlatform] = useState<"NAVER_PLACE" | "NAVER_VIEW">(platform);
    const [result, setResult] = useState<CompetitorDiscoveryItem[] | null>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const discoverMutation = useMutation({
        mutationFn: () =>
            discoverCompetitors({
                client_id: clientId,
                platform: activePlatform,
                keyword_overlap_threshold: 0.3,
                min_appearances: 3,
                top_n: 10,
                days: 30,
            }),
        onSuccess: (data) => {
            setResult(data.competitors);
            setErrorMsg(null);
        },
        onError: (err: unknown) => {
            setErrorMsg(err instanceof Error ? err.message : "분석에 실패했습니다.");
        },
    });

    const handleDiscover = () => {
        setResult(null);
        discoverMutation.mutate();
    };

    const platforms: Array<"NAVER_PLACE" | "NAVER_VIEW"> = ["NAVER_PLACE", "NAVER_VIEW"];

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <CardTitle className="flex items-center gap-2">
                        <Users className="w-5 h-5 text-blue-500" />
                        경쟁사 자동 발굴
                    </CardTitle>

                    {/* 플랫폼 토글 */}
                    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                        {platforms.map((p) => (
                            <button
                                key={p}
                                onClick={() => setActivePlatform(p)}
                                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                                    activePlatform === p
                                        ? "bg-white text-gray-900 shadow-sm"
                                        : "text-gray-500 hover:text-gray-700"
                                }`}
                            >
                                {PLATFORM_LABELS[p]}
                            </button>
                        ))}
                    </div>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                    키워드 중복도(Jaccard Similarity) 기반으로 경쟁 관계에 있는 업체를 자동으로 발굴합니다.
                </p>
            </CardHeader>

            <CardContent className="space-y-4">
                {errorMsg && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{errorMsg}</AlertDescription>
                    </Alert>
                )}

                <Button
                    onClick={handleDiscover}
                    disabled={discoverMutation.isPending}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                >
                    {discoverMutation.isPending ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            {PLATFORM_LABELS[activePlatform]} 경쟁사 분석 중...
                        </>
                    ) : (
                        <>
                            <Search className="w-4 h-4 mr-2" />
                            {PLATFORM_LABELS[activePlatform]} 경쟁사 발굴 시작
                        </>
                    )}
                </Button>

                {/* 로딩 스켈레톤 */}
                {discoverMutation.isPending && (
                    <div className="space-y-3">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-20 w-full rounded-lg" />
                        ))}
                    </div>
                )}

                {/* 결과 */}
                {result && !discoverMutation.isPending && (
                    <>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">
                                발굴된 경쟁사
                            </span>
                            <Badge variant="secondary">{result.length}개</Badge>
                        </div>

                        {result.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground text-sm">
                                경쟁사를 발굴하기 위한 키워드 데이터가 충분하지 않습니다.
                                <br />
                                플레이스 또는 블로그 키워드를 먼저 검색해 주세요.
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {result.map((item, idx) => (
                                    <CompetitorCard key={item.target_id} item={item} rank={idx + 1} />
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* 초기 안내 */}
                {!result && !discoverMutation.isPending && (
                    <div className="text-center py-6 text-sm text-muted-foreground border rounded-lg bg-gray-50">
                        버튼을 클릭하면 최근 30일 데이터를 분석해<br />
                        경쟁 업체를 자동으로 발굴합니다.
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
