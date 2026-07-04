"use client";

import { useState, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, AlertCircle, Download, X, Plus } from "lucide-react";
import {
    searchKeywords,
    KeywordSearchResult,
    RelatedKeyword,
} from "@/lib/api";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

const MAX_KEYWORDS = 10;
const MIN_KEYWORDS = 1;
const BAR_COLORS = [
    "#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a",
    "#0891b2", "#ca8a04", "#dc2626", "#4f46e5", "#059669",
];

function fmt(n: number | null | undefined): string {
    if (n === null || n === undefined) return "-";
    return n.toLocaleString("ko-KR");
}

// 마스킹("< 10") 값 정직 표기: 값이 null이면서 masked면 "< 10", 아니면 fmt.
function fmtMasked(n: number | null | undefined, masked: boolean): string {
    if (masked && (n === null || n === undefined)) return "< 10";
    return fmt(n);
}

// 실데이터 기반 워드클라우드: 검색량에 비례해 폰트 크기를 결정론적으로 산출.
// (Math.random 등 가짜 요소 없음 — 값이 바뀌면 크기도 바뀜)
function fontSizeFor(volume: number, min: number, max: number): number {
    if (max <= min) return 16;
    const ratio = (volume - min) / (max - min); // 0~1
    return Math.round(12 + ratio * 22); // 12px ~ 34px
}

export default function KeywordIntelligencePage() {
    const [inputs, setInputs] = useState<string[]>(["", ""]);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [result, setResult] = useState<KeywordSearchResult | null>(null);
    const [activeRelated, setActiveRelated] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: (kws: string[]) => searchKeywords(kws, 30),
        onSuccess: (data) => {
            setErrorMsg(null);
            setResult(data);
            const firstWithData = data.keywords.find((k) => !k.no_data);
            setActiveRelated(firstWithData?.keyword ?? data.keywords[0]?.keyword ?? null);
        },
        onError: (error: unknown) => {
            const msg =
                (error as { response?: { data?: { detail?: string } } })?.response?.data
                    ?.detail || (error instanceof Error ? error.message : "조회 중 오류가 발생했습니다.");
            setErrorMsg(msg);
            setResult(null);
        },
    });

    const cleaned = useMemo(
        () => Array.from(new Set(inputs.map((s) => s.trim()).filter(Boolean))),
        [inputs]
    );

    const handleSearch = () => {
        if (cleaned.length < MIN_KEYWORDS) {
            setErrorMsg("키워드를 최소 1개 이상 입력하세요.");
            return;
        }
        mutation.mutate(cleaned);
    };

    const updateInput = (idx: number, value: string) => {
        setInputs((prev) => prev.map((v, i) => (i === idx ? value : v)));
    };
    const addInput = () => {
        if (inputs.length < MAX_KEYWORDS) setInputs((prev) => [...prev, ""]);
    };
    const removeInput = (idx: number) => {
        setInputs((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));
    };

    // 비교 차트 데이터 (PC / 모바일 그룹 막대)
    // 비교 차트: 실측 총계가 있는 키워드만. 마스킹("<10")/데이터없음은 0으로 왜곡 표시하지 않고 제외.
    const chartData = useMemo(() => {
        if (!result) return [];
        return result.keywords
            .filter((k) => !k.no_data && !k.masked && k.monthly_total !== null)
            .map((k) => ({
                keyword: k.keyword,
                PC: k.monthly_pc ?? 0,
                모바일: k.monthly_mobile ?? 0,
            }));
    }, [result]);

    // 차트에서 제외된(마스킹/데이터없음) 키워드 목록 — 사용자에게 정직히 고지
    const excludedFromChart = useMemo(
        () => (result ? result.keywords.filter((k) => k.no_data || k.masked).map((k) => k.keyword) : []),
        [result]
    );

    // 엑셀(CSV, UTF-8 BOM) 다운로드 — 화면 조회 데이터 그대로. 가공/추정 없음.
    const downloadCsv = () => {
        if (!result) return;
        const rows: string[][] = [];
        rows.push(["구분", "키워드", "PC 월간검색수", "모바일 월간검색수", "합계", "경쟁정도", "최초 검색일"]);
        result.keywords.forEach((k) => {
            rows.push([
                "검색키워드",
                k.keyword,
                fmtMasked(k.monthly_pc, k.masked),
                fmtMasked(k.monthly_mobile, k.masked),
                k.no_data ? "데이터없음" : fmtMasked(k.monthly_total, k.masked),
                k.no_data ? "데이터없음" : k.comp_idx ?? "-",
                k.first_seen ?? "이번이 최초",
            ]);
        });
        rows.push([]);
        Object.entries(result.related).forEach(([base, items]) => {
            items.forEach((r) => {
                rows.push([
                    "연관키워드",
                    `${base} > ${r.keyword}`,
                    "",
                    "",
                    fmtMasked(r.monthly_total, r.masked),
                    "",
                    "",
                ]);
            });
        });
        const csv = rows.map((r) => r.map((c) => `"${(c ?? "").replace(/"/g, '""')}"`).join(",")).join("\r\n");
        const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `keyword_search_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const relatedItems: RelatedKeyword[] = activeRelated
        ? result?.related[activeRelated] ?? []
        : [];
    const relMax = relatedItems.length ? Math.max(...relatedItems.map((r) => r.monthly_total ?? 0)) : 0;
    const relMin = relatedItems.length ? Math.min(...relatedItems.map((r) => r.monthly_total ?? 0)) : 0;

    return (
        <div className="space-y-6 p-6">
            <div>
                <h1 className="text-2xl font-bold">키워드 검색량 분석</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    최대 {MAX_KEYWORDS}개 키워드의 월간 검색수(PC/모바일)와 연관키워드를 조회합니다.
                    <span className="ml-1 text-emerald-600">
                        · 출처: 네이버 검색광고 키워드도구 API (실측)
                    </span>
                </p>
            </div>

            {/* 다중 키워드 입력 */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">키워드 입력 (1~{MAX_KEYWORDS}개)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {inputs.map((val, idx) => (
                            <div key={idx} className="flex items-center gap-1">
                                <Input
                                    value={val}
                                    placeholder={`키워드 ${idx + 1}`}
                                    onChange={(e) => updateInput(idx, e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                                />
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => removeInput(idx)}
                                    disabled={inputs.length <= 1}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={addInput}
                            disabled={inputs.length >= MAX_KEYWORDS}
                        >
                            <Plus className="h-4 w-4 mr-1" /> 키워드 추가
                        </Button>
                        <Button onClick={handleSearch} disabled={mutation.isPending}>
                            {mutation.isPending ? (
                                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                            ) : (
                                <Search className="h-4 w-4 mr-1" />
                            )}
                            검색 ({cleaned.length})
                        </Button>
                        {result && (
                            <Button variant="secondary" onClick={downloadCsv}>
                                <Download className="h-4 w-4 mr-1" /> 엑셀(CSV) 다운로드
                            </Button>
                        )}
                    </div>
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
                    {/* 검색량 비교 차트 */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">최근 30일 월간검색수 비교</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {chartData.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                    검색량 데이터가 있는 키워드가 없습니다.
                                </p>
                            ) : (
                                <ResponsiveContainer width="100%" height={320}>
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="keyword" />
                                        <YAxis tickFormatter={(v) => v.toLocaleString("ko-KR")} />
                                        <Tooltip formatter={(v) => Number(v ?? 0).toLocaleString("ko-KR")} />
                                        <Legend />
                                        <Bar dataKey="PC" fill="#93c5fd" />
                                        <Bar dataKey="모바일" fill="#2563eb" />
                                    </BarChart>
                                </ResponsiveContainer>
                            )}
                            {excludedFromChart.length > 0 && (
                                <p className="text-xs text-muted-foreground mt-2">
                                    ※ 비교 차트 제외: {excludedFromChart.join(", ")} (검색수 10 미만 또는 데이터 없음)
                                </p>
                            )}
                        </CardContent>
                    </Card>

                    {/* 상세 테이블 */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">키워드별 상세</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b text-left text-muted-foreground">
                                            <th className="py-2 pr-4">키워드</th>
                                            <th className="py-2 pr-4 text-right">PC</th>
                                            <th className="py-2 pr-4 text-right">모바일</th>
                                            <th className="py-2 pr-4 text-right">합계</th>
                                            <th className="py-2 pr-4">경쟁정도</th>
                                            <th className="py-2 pr-4">최초 검색일</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.keywords.map((k, i) => (
                                            <tr
                                                key={k.keyword}
                                                className="border-b cursor-pointer hover:bg-muted/50"
                                                onClick={() => setActiveRelated(k.keyword)}
                                            >
                                                <td className="py-2 pr-4 font-medium">
                                                    <span
                                                        className="inline-block w-2 h-2 rounded-full mr-2"
                                                        style={{ background: BAR_COLORS[i % BAR_COLORS.length] }}
                                                    />
                                                    {k.keyword}
                                                </td>
                                                <td className="py-2 pr-4 text-right">{fmtMasked(k.monthly_pc, k.masked)}</td>
                                                <td className="py-2 pr-4 text-right">{fmtMasked(k.monthly_mobile, k.masked)}</td>
                                                <td className="py-2 pr-4 text-right font-semibold">
                                                    {fmtMasked(k.monthly_total, k.masked)}
                                                </td>
                                                <td className="py-2 pr-4">
                                                    {k.no_data ? (
                                                        <Badge variant="outline">데이터없음</Badge>
                                                    ) : (
                                                        k.comp_idx ?? "-"
                                                    )}
                                                </td>
                                                <td className="py-2 pr-4 text-muted-foreground">
                                                    {k.first_seen ?? (
                                                        <Badge variant="secondary">이번이 최초</Badge>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>

                    {/* 연관키워드 워드클라우드 */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">
                                연관키워드 {activeRelated ? `— "${activeRelated}"` : ""}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-wrap gap-2 mb-4">
                                {result.keywords.map((k) => (
                                    <Button
                                        key={k.keyword}
                                        size="sm"
                                        variant={activeRelated === k.keyword ? "default" : "outline"}
                                        onClick={() => setActiveRelated(k.keyword)}
                                    >
                                        {k.keyword}
                                    </Button>
                                ))}
                            </div>
                            {relatedItems.length === 0 ? (
                                <p className="text-sm text-muted-foreground">연관키워드가 없습니다.</p>
                            ) : (
                                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                                    {relatedItems.map((r) => (
                                        <span
                                            key={r.keyword}
                                            title={`월간검색수 ${fmtMasked(r.monthly_total, r.masked)}`}
                                            className="text-foreground hover:text-blue-600 transition-colors"
                                            style={{
                                                fontSize: `${fontSizeFor(r.monthly_total ?? 0, relMin, relMax)}px`,
                                                lineHeight: 1.3,
                                            }}
                                        >
                                            {r.keyword}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
