"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, AlertCircle, Youtube, CheckCircle2, XCircle } from "lucide-react";
import { getYouTubeStats, getSnsStatus, YouTubeStats } from "@/lib/api";
import { ConnectPrompt } from "@/components/ui/ConnectPrompt";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

const CHANNEL_LABELS: Record<string, string> = {
    youtube: "유튜브",
    x: "엑스(X)",
    instagram: "인스타그램",
    tiktok: "틱톡",
};

function fmt(n: number): string {
    return n.toLocaleString("ko-KR");
}

export default function SnsPage() {
    const [keyword, setKeyword] = useState("");
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [result, setResult] = useState<YouTubeStats | null>(null);

    const { data: status } = useQuery({
        queryKey: ["sns-status"],
        queryFn: getSnsStatus,
        refetchOnWindowFocus: false,
    });

    const mutation = useMutation({
        mutationFn: (kw: string) => getYouTubeStats(kw, 25),
        onSuccess: (data) => {
            setErrorMsg(null);
            setResult(data);
        },
        onError: (e: unknown) => {
            const msg =
                (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                (e instanceof Error ? e.message : "조회 오류");
            setErrorMsg(msg);
            setResult(null);
        },
    });

    const monthData = result
        ? Object.entries(result.by_upload_month).map(([k, v]) => ({
              month: k,
              영상수: v.videos,
              조회수: v.views,
          }))
        : [];

    return (
        <div className="space-y-6 p-6">
            <div>
                <h1 className="text-2xl font-bold">SNS 언급량 분석</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    4대 SNS 매체 검색어 언급량/반응 (RFP 2-2)
                </p>
            </div>

            {/* 매체별 연동 상태 — 실제 상태만 정직하게 표기 */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">매체별 연동 상태</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        {status &&
                            Object.entries(status).map(([key, s]) => (
                                <div key={key} className="border rounded-lg p-3">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-medium">{CHANNEL_LABELS[key] ?? key}</span>
                                        {s.configured ? (
                                            <Badge className="bg-emerald-600">연동됨</Badge>
                                        ) : s.supported ? (
                                            <Badge variant="outline">키 필요</Badge>
                                        ) : (
                                            <Badge variant="destructive">벤더 필요</Badge>
                                        )}
                                    </div>
                                    <p className="text-xs text-muted-foreground">{s.method}</p>
                                    {!s.configured && (
                                        <p className="text-[11px] text-primary mt-1.5 font-medium">
                                            {s.supported
                                                ? "고객님의 API 키 연동 시 실측 데이터가 표출됩니다."
                                                : "전문 데이터 벤더 연동 시 실측 데이터가 표출됩니다."}
                                        </p>
                                    )}
                                </div>
                            ))}
                    </div>
                </CardContent>
            </Card>

            {/* 유튜브 검색 */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                        <Youtube className="h-5 w-5 text-red-600" /> 유튜브 검색어 분석
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {status && !status.youtube?.configured ? (
                        // YouTube 미연동 — 검색 대신 전문 연동 안내 (503 대신 명확한 가이드)
                        <ConnectPrompt
                            source="YouTube Data API 키"
                            description="고객님의 YouTube Data API 키를 연동하시면 검색어 포함 영상수·조회수 실측 데이터가 표출됩니다."
                            actionHint="[설정 > 데이터 수집]"
                        />
                    ) : (
                        <>
                            <div className="flex gap-2">
                                <Input
                                    value={keyword}
                                    placeholder="검색어 입력 (예: 다이어트)"
                                    onChange={(e) => setKeyword(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && keyword.trim() && mutation.mutate(keyword.trim())}
                                />
                                <Button
                                    onClick={() => keyword.trim() && mutation.mutate(keyword.trim())}
                                    disabled={mutation.isPending}
                                >
                                    {mutation.isPending ? (
                                        <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                    ) : (
                                        <Search className="h-4 w-4 mr-1" />
                                    )}
                                    검색
                                </Button>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                ⚠️ 총 영상수는 유튜브 공식 근사치, 조회수는 현재 누적값(시점별 추이 아님)입니다.
                            </p>
                        </>
                    )}
                </CardContent>
            </Card>

            {errorMsg && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{errorMsg}</AlertDescription>
                </Alert>
            )}

            {result && (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-xs text-muted-foreground">검색어 포함 영상 (근사)</p>
                                <p className="text-2xl font-bold">{fmt(result.total_matching_approx)}</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-xs text-muted-foreground">상위 {result.sampled_count}개 조회수 합</p>
                                <p className="text-2xl font-bold">{fmt(result.total_views_sampled)}</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-xs text-muted-foreground">샘플 영상 수</p>
                                <p className="text-2xl font-bold">{fmt(result.sampled_count)}</p>
                            </CardContent>
                        </Card>
                    </div>

                    {monthData.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">업로드 월별 영상수 / 누적 조회수</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={monthData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="month" fontSize={11} />
                                        <YAxis yAxisId="left" orientation="left" />
                                        <YAxis yAxisId="right" orientation="right" />
                                        <Tooltip formatter={(v) => Number(v ?? 0).toLocaleString("ko-KR")} />
                                        <Bar yAxisId="left" dataKey="영상수" fill="#dc2626" />
                                        <Bar yAxisId="right" dataKey="조회수" fill="#f59e0b" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    )}

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">상위 영상 (조회수 순)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b text-left text-muted-foreground">
                                            <th className="py-2 pr-4">제목</th>
                                            <th className="py-2 pr-4">채널</th>
                                            <th className="py-2 pr-4 text-right">조회수</th>
                                            <th className="py-2 pr-4 text-right">좋아요</th>
                                            <th className="py-2 pr-4">업로드</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.videos.map((v) => (
                                            <tr key={v.videoId} className="border-b hover:bg-muted/50">
                                                <td className="py-2 pr-4 max-w-xs truncate">
                                                    <a
                                                        href={`https://www.youtube.com/watch?v=${v.videoId}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-600 hover:underline"
                                                    >
                                                        {v.title ?? "(제목 없음)"}
                                                    </a>
                                                </td>
                                                <td className="py-2 pr-4">{v.channel ?? "-"}</td>
                                                <td className="py-2 pr-4 text-right font-medium">{fmt(v.viewCount)}</td>
                                                <td className="py-2 pr-4 text-right">{fmt(v.likeCount)}</td>
                                                <td className="py-2 pr-4">{v.publishedAt?.slice(0, 10)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
