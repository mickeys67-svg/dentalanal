"use client";

import { KeywordRank } from "@/types";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { ExternalLink, Search } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface KeywordRankTableProps {
    data: KeywordRank[];
    isLoading: boolean;
    keyword?: string;
}

export function KeywordRankTable({ data, isLoading, keyword }: KeywordRankTableProps) {
    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-3">
                    <Skeleton className="h-6 w-48" />
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {[...Array(5)].map((_, i) => (
                            <Skeleton key={i} className="h-12 w-full" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="w-full h-64 flex flex-col items-center justify-center border rounded-xl border-dashed bg-gray-50/50">
                <div className="bg-white p-4 rounded-full shadow-sm mb-3">
                    <Search className="w-6 h-6 text-gray-400" />
                </div>
                <p className="text-gray-900 font-semibold">데이터가 없습니다</p>
                <p className="text-sm text-gray-500 mt-1">키워드를 입력하고 조사를 시작하여 순위를 추적하세요.</p>
            </div>
        );
    }

    return (
        <Card className="overflow-hidden border-none shadow-sm ring-1 ring-gray-200">
            <CardHeader className="bg-gray-50/50 pb-4 border-b">
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <CardTitle className="text-lg font-bold text-gray-900">
                            &apos;{keyword}&apos; 검색 결과
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                            실시간 네이버 플레이스 노출 순위
                        </p>
                    </div>
                    <Badge variant="outline" className="bg-white hover:bg-white font-mono text-xs text-gray-500">
                        {format(new Date(), "yyyy-MM-dd HH:mm")} 업데이트
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <Table>
                    <TableHeader className="bg-gray-50">
                        <TableRow>
                            <TableHead className="w-[80px] text-center font-semibold text-gray-600">순위</TableHead>
                            <TableHead className="font-semibold text-gray-600">업체명 (Title)</TableHead>
                            <TableHead className="hidden md:table-cell font-semibold text-gray-600">카테고리</TableHead>
                            <TableHead className="text-center font-semibold text-gray-600">변동</TableHead>
                            <TableHead className="text-right font-semibold text-gray-600">링크</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.map((item, index) => {
                            const isTop3 = index < 3;
                            const rankBadgeColor =
                                index === 0 ? "bg-yellow-100 text-yellow-700 ring-yellow-200" :
                                    index === 1 ? "bg-gray-100 text-gray-700 ring-gray-200" :
                                        index === 2 ? "bg-orange-100 text-orange-800 ring-orange-200" :
                                            "bg-white text-gray-500 ring-gray-100";

                            // Random mock change for UI demo since we don't have historical data store fully linked yet in this view
                            // In real app, this comes from DB comparison
                            // Random mock change logic removed as it was unused
                            // const mockChange = Math.random() > 0.7 ? (Math.random() > 0.5 ? 1 : -1) : 0;

                            return (
                                <TableRow key={index} className="hover:bg-gray-50 transition-colors">
                                    <TableCell className="text-center py-4">
                                        <div className={`
                                            w-8 h-8 rounded-full flex items-center justify-center mx-auto font-bold text-sm ring-1 ring-inset
                                            ${rankBadgeColor}
                                        `}>
                                            {item.rank}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <span className={`font-semibold ${isTop3 ? 'text-gray-900' : 'text-gray-600'}`}>
                                                {item.title}
                                            </span>
                                            {isTop3 && (
                                                <span className="text-[10px] text-blue-600 font-medium mt-0.5">Premium Rank</span>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="hidden md:table-cell text-muted-foreground text-sm">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="secondary" className="font-normal text-xs bg-gray-100 text-gray-500 hover:bg-gray-100">
                                                {item.blog_name || "플레이스"}
                                            </Badge>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-center">
                                        {/* Placeholder for Rank Change - requires history */}
                                        <div className="flex items-center justify-center gap-1 text-xs font-medium text-gray-400">
                                            -
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        {item.link ? (
                                            <a
                                                href={item.link}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors"
                                            >
                                                방문
                                                <ExternalLink className="w-3 h-3" />
                                            </a>
                                        ) : (
                                            <span className="text-xs text-gray-300">-</span>
                                        )}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
