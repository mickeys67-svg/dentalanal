"use client";

import { useState, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Loader2, AlertCircle, Info } from "lucide-react";
import {
    getKeywordTrend,
    getKeywordDemographics,
    TrendResult,
    DemographicsResult,
} from "@/lib/api";
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

const COLORS = [
    "#2563eb", "#db2777", "#16a34a", "#ea580c", "#7c3aed",
    "#0891b2", "#ca8a04", "#dc2626", "#4f46e5", "#059669",
    "#9333ea", "#0d9488",
];

const AGES_OPTIONS: { code: string; label: string }[] = [
    { code: "2", label: "13-18" },
    { code: "3", label: "19-24" },
    { code: "4", label: "25-29" },
    { code: "5", label: "30-34" },
    { code: "6", label: "35-39" },
    { code: "7", label: "40-44" },
    { code: "8", label: "45-49" },
    { code: "9", label: "50-54" },
    { code: "10", label: "55-59" },
    { code: "11", label: "60+" },
];

function isoDaysAgo(days: number): string {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().slice(0, 10);
}

export default function TrendAnalysisPage() {
    const [inputs, setInputs] = useState<string[]>(["", ""]);
    const [startDate, setStartDate] = useState(isoDaysAgo(30));
    const [endDate, setEndDate] = useState(isoDaysAgo(1));
    const [timeUnit, setTimeUnit] = useState<"date" | "week" | "month">("date");
    const [device, setDevice] = useState<"" | "pc" | "mo">("");
    const [gender, setGender] = useState<"" | "m" | "f">("");
    const [ages, setAges] = useState<string[]>([]);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [trend, setTrend] = useState<TrendResult | null>(null);
    const [demo, setDemo] = useState<DemographicsResult | null>(null);
    const [selectedKw, setSelectedKw] = useState<string | null>(null);

    const cleaned = useMemo(
        () => Array.from(new Set(inputs.map((s) => s.trim()).filter(Boolean))).slice(0, 5),
        [inputs]
    );

    const trendMutation = useMutation({
        mutationFn: () =>
            getKeywordTrend({
                keywords: cleaned,
                start_date: startDate,
                end_date: endDate,
                time_unit: timeUnit,
                device,
                gender,
                ages: ages.length ? ages : undefined,
            }),
        onSuccess: (data) => {
            setErrorMsg(null);
            setTrend(data);
            const first = data.results[0]?.keyword ?? null;
            setSelectedKw(first);
            if (first) demoMutation.mutate(first);
        },
        onError: (e: unknown) => {
            const msg =
                (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                (e instanceof Error ? e.message : "조회 오류");
            setErrorMsg(msg);
            setTrend(null);
            setDemo(null);
        },
    });

    const demoMutation = useMutation({
        mutationFn: (kw: string) => getKeywordDemographics(kw, startDate, endDate),
        onSuccess: (data) => setDemo(data),
        onError: () => setDemo(null),
    });

    const handleSearch = () => {
        if (cleaned.length === 0) {
            setErrorMsg("키워드를 최소 1개 입력하세요.");
            return;
        }
        trendMutation.mutate();
    };

    const toggleAge = (code: string) =>
        setAges((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));

    // 라인차트용: period 축 병합
    const lineData = useMemo(() => {
        if (!trend) return [];
        const periodMap: Record<string, Record<string, number | string>> = {};
        trend.results.forEach((r) => {
            r.series.forEach((p) => {
                if (!periodMap[p.period]) periodMap[p.period] = { period: p.period };
                periodMap[p.period][r.keyword] = p.ratio;
            });
        });
        return Object.values(periodMap).sort((a, b) =>
            String(a.period).localeCompare(String(b.period))
        );
    }, [trend]);

    const selected = trend?.results.find((r) => r.keyword === selectedKw) ?? null;
    const monthData = selected
        ? Object.entries(selected.by_month).map(([k, v]) => ({ name: k, value: v }))
        : [];
    const dowOrder = ["월", "화", "수", "목", "금", "토", "일"];
    const dowData = selected
        ? dowOrder
              .filter((d) => d in selected.by_dow)
              .map((d) => ({ name: d, value: selected.by_dow[d] }))
        : [];

    return (
        <div className="space-y-6 p-6">
            <div>
                <h1 className="text-2xl font-bold">검색 트렌드 분석</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    네이버 데이터랩 검색어트렌드 — 기간·성별·연령·기기 필터
                    <span className="ml-1 text-emerald-600">· 출처: 네이버 데이터랩 (실측)</span>
                </p>
            </div>

            {/* 상대지수 안내 배너 (가짜 데이터 금지: 절대량 아님을 명시) */}
            <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                    모든 수치는 <b>상대지수(0~100)</b>입니다. 기간 내 최대 검색일을 100으로 정규화한 값으로,
                    <b> 절대 검색수가 아닙니다.</b> 성별·연령대 값은 세그먼트별 <b>상대 관심도 지수</b>이며 인구 비율이 아닙니다.
                    (절대 월간검색수는 &ldquo;키워드 검색량&rdquo; 메뉴 참고)
                </AlertDescription>
            </Alert>

            {/* 입력 & 필터 */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">조회 조건</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
                        {inputs.map((val, idx) => (
                            <Input
                                key={idx}
                                value={val}
                                placeholder={`키워드 ${idx + 1}`}
                                onChange={(e) =>
                                    setInputs((prev) => prev.map((v, i) => (i === idx ? e.target.value : v)))
                                }
                                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            />
                        ))}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => inputs.length < 5 && setInputs((p) => [...p, ""])}
                            disabled={inputs.length >= 5}
                        >
                            키워드 추가 (최대 5)
                        </Button>
                    </div>

                    <div className="flex flex-wrap items-end gap-3">
                        <label className="text-xs">
                            시작일
                            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                        </label>
                        <label className="text-xs">
                            종료일
                            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
                        </label>
                        <div className="flex gap-1">
                            {(["date", "week", "month"] as const).map((u) => (
                                <Button
                                    key={u}
                                    size="sm"
                                    variant={timeUnit === u ? "default" : "outline"}
                                    onClick={() => setTimeUnit(u)}
                                >
                                    {u === "date" ? "일별" : u === "week" ? "주별" : "월별"}
                                </Button>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground mr-1">기기</span>
                            {([["", "전체"], ["pc", "PC"], ["mo", "모바일"]] as const).map(([v, l]) => (
                                <Button key={v} size="sm" variant={device === v ? "default" : "outline"} onClick={() => setDevice(v)}>
                                    {l}
                                </Button>
                            ))}
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground mr-1">성별</span>
                            {([["", "전체"], ["m", "남성"], ["f", "여성"]] as const).map(([v, l]) => (
                                <Button key={v} size="sm" variant={gender === v ? "default" : "outline"} onClick={() => setGender(v)}>
                                    {l}
                                </Button>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-1">
                        <span className="text-xs text-muted-foreground mr-1">연령대</span>
                        {AGES_OPTIONS.map((a) => (
                            <Button
                                key={a.code}
                                size="sm"
                                variant={ages.includes(a.code) ? "default" : "outline"}
                                onClick={() => toggleAge(a.code)}
                            >
                                {a.label}
                            </Button>
                        ))}
                    </div>

                    <Button onClick={handleSearch} disabled={trendMutation.isPending}>
                        {trendMutation.isPending ? (
                            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        ) : (
                            <Search className="h-4 w-4 mr-1" />
                        )}
                        트렌드 조회
                    </Button>
                </CardContent>
            </Card>

            {errorMsg && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{errorMsg}</AlertDescription>
                </Alert>
            )}

            {trend && (
                <>
                    {/* 추이 라인차트 */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">검색 추이 (상대지수 0~100)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={340}>
                                <LineChart data={lineData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="period" fontSize={11} />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    {trend.results.map((r, i) => (
                                        <Line
                                            key={r.keyword}
                                            type="monotone"
                                            dataKey={r.keyword}
                                            stroke={COLORS[i % COLORS.length]}
                                            dot={false}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* 키워드 선택 */}
                    <div className="flex flex-wrap gap-2">
                        {trend.results.map((r) => (
                            <Button
                                key={r.keyword}
                                size="sm"
                                variant={selectedKw === r.keyword ? "default" : "outline"}
                                onClick={() => {
                                    setSelectedKw(r.keyword);
                                    demoMutation.mutate(r.keyword);
                                }}
                            >
                                {r.keyword}
                            </Button>
                        ))}
                    </div>

                    {/* 월별 / 요일별 원형차트 */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">월별 분포 {selectedKw && `— ${selectedKw}`}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {monthData.length === 0 ? (
                                    <p className="text-sm text-muted-foreground">데이터 없음</p>
                                ) : (
                                    <ResponsiveContainer width="100%" height={260}>
                                        <PieChart>
                                            <Pie data={monthData} dataKey="value" nameKey="name" outerRadius={90} label>
                                                {monthData.map((_, i) => (
                                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                )}
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">요일별 분포 {selectedKw && `— ${selectedKw}`}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {dowData.length === 0 ? (
                                    <p className="text-sm text-muted-foreground">
                                        일별(date) 단위 조회 시에만 요일 분포가 표시됩니다.
                                    </p>
                                ) : (
                                    <ResponsiveContainer width="100%" height={260}>
                                        <PieChart>
                                            <Pie data={dowData} dataKey="value" nameKey="name" outerRadius={90} label>
                                                {dowData.map((_, i) => (
                                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* 성별 / 연령대 관심도 */}
                    {demo?.partial && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription className="text-xs">
                                일부 세그먼트 조회에 실패했습니다(레이트리밋 등). 실패한 항목은 값이 비어 있으며,
                                이는 &ldquo;관심도 0&rdquo;이 아니라 <b>미조회</b>입니다. 잠시 후 다시 시도하세요.
                            </AlertDescription>
                        </Alert>
                    )}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">성별 상대 관심도 {demo && `— ${demo.keyword}`}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {demoMutation.isPending ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : demo && demo.gender.some((g) => g.index !== null) ? (
                                    <ResponsiveContainer width="100%" height={220}>
                                        <BarChart data={demo.gender}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="segment" />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="index" fill="#2563eb" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <p className="text-sm text-muted-foreground">데이터 없음</p>
                                )}
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">연령대 상대 관심도 {demo && `— ${demo.keyword}`}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {demoMutation.isPending ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : demo && demo.age.some((a) => a.index !== null) ? (
                                    <ResponsiveContainer width="100%" height={220}>
                                        <BarChart data={demo.age}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="segment" fontSize={10} />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="index" fill="#db2777" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <p className="text-sm text-muted-foreground">데이터 없음</p>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    );
}
