"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getEfficiencyReview,
    createCollaborativeTask
} from '@/lib/api';
import { toast } from 'sonner';
import { useClient } from '@/components/providers/ClientProvider';
import {
    EfficiencyReview,
    EfficiencyItem,
} from '@/types';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ScatterChart, Scatter, ZAxis, Cell, Legend
} from 'recharts';
import {
    Zap, TrendingUp, Target, DollarSign,
    MessageSquare, AlertCircle, Loader2, Sparkles,
    ChevronRight, ArrowUpRight, ArrowDownRight, BarChart3, Plus
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';
import clsx from 'clsx';

export default function EfficiencyPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [days, setDays] = useState(30);
    const [processingTaskId, setProcessingTaskId] = useState<string | null>(null);

    const { data: review, isLoading, error } = useQuery<EfficiencyReview>({
        queryKey: ['efficiency-review', selectedClient?.id, days],
        queryFn: () => getEfficiencyReview(selectedClient!.id, days),
        enabled: !!selectedClient
    });

    const taskMutation = useMutation({
        mutationFn: (data: { title: string, content: string }) =>
            createCollaborativeTask(selectedClient!.id, {
                title: data.title,
                status: 'PENDING',
                owner: '마케팅팀',
                deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
            }),
        onSuccess: () => {
            toast.success('업무가 협업 보드에 등록되었습니다.');
            setProcessingTaskId(null);
        },
        onError: () => {
            toast.error('업무 등록에 실패했습니다.');
            setProcessingTaskId(null);
        }
    });

    const handleCreateTask = (item: EfficiencyItem) => {
        if (!item.suggestion) return;
        setProcessingTaskId(item.name);
        taskMutation.mutate({
            title: `[광고 최적화] ${item.name}`,
            content: item.suggestion
        });
    };

    if (!selectedClient) {
        return <EmptyClientPlaceholder title="분석할 업체를 선택해주세요" description="업체를 선택하면 실시간 성과 지표와 효율 리뷰를 확인할 수 있습니다." />;
    }

    if (isLoading) {
        return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-12 bg-red-50 rounded-3xl border border-red-100">
                <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
                <h3 className="font-bold text-red-900 mb-2">분석 데이터를 불러오지 못했습니다</h3>
                <p className="text-red-600 text-sm mb-6">서버 연결 상태를 확인하거나 잠시 후 다시 시도해주세요.</p>
                <button
                    onClick={() => queryClient.invalidateQueries({ queryKey: ['efficiency-review'] })}
                    className="px-6 py-2 bg-red-600 text-white rounded-xl text-sm font-bold hover:bg-red-700 transition-all"
                >
                    다시 시도
                </button>
            </div>
        );
    }

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload as EfficiencyItem;
            return (
                <div className="bg-white p-4 shadow-xl border border-gray-100 rounded-2xl">
                    <p className="font-bold text-gray-900 mb-2">{data.name}</p>
                    <div className="space-y-1 text-xs">
                        <div className="flex justify-between gap-4">
                            <span className="text-gray-400">비용:</span>
                            <span className="font-mono font-bold text-gray-900">₩{data.spend.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                            <span className="text-gray-400">전환:</span>
                            <span className="font-bold text-indigo-600">{data.conversions}건</span>
                        </div>
                        <div className="flex justify-between gap-4 border-t border-gray-50 pt-1 mt-1">
                            <span className="text-gray-400">ROAS:</span>
                            <span className="font-black text-primary">{data.roas}%</span>
                        </div>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        성과 효율 리뷰 <Zap className="w-5 h-5 text-amber-400 fill-amber-400" />
                    </h1>
                    <p className="text-sm text-gray-500">{review?.period || '성과 지표 분석 중...'}</p>
                </div>
                <div className="flex bg-gray-100 p-1 rounded-xl">
                    {[7, 30, 90].map((d) => (
                        <button
                            key={d}
                            onClick={() => setDays(d)}
                            className={clsx(
                                "px-4 py-1.5 text-xs font-bold rounded-lg transition-all",
                                days === d ? "bg-white text-primary shadow-sm" : "text-gray-400 hover:text-gray-600"
                            )}
                        >
                            {d === 30 ? '한 달' : d === 7 ? '일주일' : '분기'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Top Summaries */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <EfficiencyCard
                    title="전체 ROAS"
                    value={`${review?.overall_roas || 0}%`}
                    icon={TrendingUp}
                    color="primary"
                    subtitle="지난 기간 대비 +12%"
                />
                <EfficiencyCard
                    title="총 전환수"
                    value={`${review?.total_conversions || 0}건`}
                    icon={Target}
                    color="indigo"
                    subtitle="유효 상담 포함"
                />
                <EfficiencyCard
                    title="총 광고비"
                    value={`₩${(review?.total_spend || 0).toLocaleString()}`}
                    icon={DollarSign}
                    color="blue"
                    subtitle="매체 집행액 기준"
                />
                <div className="bg-gradient-to-br from-indigo-600 to-violet-700 p-6 rounded-3xl shadow-xl shadow-indigo-100 text-white relative overflow-hidden">
                    <div className="relative z-10">
                        <h3 className="text-xs font-bold text-indigo-100 mb-1 uppercase tracking-widest">AI INSIGHT</h3>
                        <p className="text-sm font-medium leading-relaxed opacity-90">
                            현재 {(review?.overall_roas || 0) > 500 ? '매우 우수한' : '개선 작업이 필요한'} 효율을 보여주고 있습니다.
                        </p>
                    </div>
                    <Sparkles className="absolute -bottom-2 -right-2 w-20 h-20 text-white opacity-10 rotate-12" />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Efficiency Matrix */}
                <div className="lg:col-span-2">
                    <DashboardWidget title="효율성 매트릭스 (Efficiency Matrix)" subtitle="비용 대비 전환 성과 분포도. 우측 상단일수록 고효율 캠페인입니다.">
                        <div className="h-[400px] mt-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                                    <XAxis
                                        type="number"
                                        dataKey="spend"
                                        name="비용"
                                        unit="원"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                    />
                                    <YAxis
                                        type="number"
                                        dataKey="conversions"
                                        name="전환"
                                        unit="건"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                    />
                                    <ZAxis type="number" dataKey="roas" range={[50, 400]} name="ROAS" />
                                    <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                                    <Scatter name="캠페인" data={review?.items || []}>
                                        {review?.items?.map((entry: EfficiencyItem, index: number) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.roas > 500 ? '#10B981' : entry.roas > 300 ? '#6366F1' : '#F59E0B'}
                                            />
                                        ))}
                                    </Scatter>
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    </DashboardWidget>
                </div>

                {/* AI Detailed Review */}
                <div className="lg:col-span-1">
                    <div className="bg-white h-full rounded-3xl border border-gray-100 shadow-sm flex flex-col">
                        <div className="p-6 border-b border-gray-50 flex items-center justify-between">
                            <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                <MessageSquare className="w-4 h-4 text-primary" /> Gemini 성과 비평
                            </h3>
                            <div className="flex gap-1">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                <div className="text-[10px] font-black text-gray-400">ANALYZING</div>
                            </div>
                        </div>
                        <div className="p-6 overflow-y-auto max-h-[450px] scrollbar-hide flex-1">
                            <div className="prose prose-sm prose-indigo max-w-none prose-p:leading-relaxed prose-li:my-1 text-gray-600">
                                <ReactMarkdown>
                                    {review?.ai_review || '데이터 분석 중... 잠시만 기다려주세요.'}
                                </ReactMarkdown>
                            </div>
                        </div>
                        <div className="p-4 bg-gray-50 border-t border-gray-50 text-[10px] text-gray-400 text-center rounded-b-3xl">
                            위 분석은 실시간 광고 집행 성능 데이터를 기반으로 생성되었습니다.
                        </div>
                    </div>
                </div>
            </div>

            {/* Detailed Performance List */}
            <DashboardWidget title="캠페인별 성과 및 AI 최적화 제안" subtitle="매체별 상세 효율 지표와 AI가 제안하는 즉시 개선 액션입니다.">
                <div className="overflow-x-auto mt-4">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50">
                                <th className="py-4 px-2">캠페인 및 매체</th>
                                <th className="py-4">집행 비용 / ROAS</th>
                                <th className="py-4">AI 최적화 제안 (Action Item)</th>
                                <th className="py-4 text-right">관리</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50 text-sm">
                            {review?.items?.map((item: EfficiencyItem, i: number) => (
                                <tr key={i} className="hover:bg-gray-50/50 transition-all group">
                                    <td className="py-6 px-2 w-[25%]">
                                        <div className="font-bold text-gray-900 group-hover:text-primary transition-colors">{item.name}</div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={clsx(
                                                "px-2 py-0.5 rounded text-[9px] font-black",
                                                item.roas > 500 ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                                            )}>
                                                ROAS {item.roas}%
                                            </span>
                                            <span className="text-[10px] text-gray-400 font-mono">₩{item.spend.toLocaleString()}</span>
                                        </div>
                                    </td>
                                    <td className="py-6 w-[20%]">
                                        <div className="flex flex-col gap-1">
                                            <div className="flex justify-between text-[11px] pr-8">
                                                <span className="text-gray-400">CTR</span>
                                                <span className="font-bold">{item.ctr}%</span>
                                            </div>
                                            <div className="flex justify-between text-[11px] pr-8">
                                                <span className="text-gray-400">CVR</span>
                                                <span className="font-bold text-indigo-600">{item.cvr}%</span>
                                            </div>
                                            <div className="flex justify-between text-[11px] pr-8">
                                                <span className="text-gray-400">CPA</span>
                                                <span className="font-bold">₩{item.cpa.toLocaleString()}</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-6 px-4">
                                        {item.suggestion ? (
                                            <div className="bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100/50 relative group/sug">
                                                <div className="text-xs text-indigo-900 leading-relaxed font-medium">
                                                    <span className="inline-flex items-center gap-1 bg-indigo-600 text-white text-[9px] px-1.5 py-0.5 rounded mr-2 font-black uppercase">Suggestion</span>
                                                    {item.suggestion}
                                                </div>
                                                <div className="absolute top-2 right-2 opacity-0 group-hover/sug:opacity-100 transition-opacity">
                                                    <Sparkles className="w-3 h-3 text-indigo-400" />
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="text-xs text-gray-400 italic">충분한 데이터 수집 후 제안이 생성됩니다.</div>
                                        )}
                                    </td>
                                    <td className="py-6 text-right px-4">
                                        {item.suggestion && (
                                            <button
                                                onClick={() => handleCreateTask(item)}
                                                disabled={processingTaskId === item.name}
                                                className="flex items-center gap-2 bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-xl text-[11px] font-bold hover:bg-gray-50 hover:border-primary hover:text-primary transition-all shadow-sm active:scale-95 disabled:opacity-50"
                                            >
                                                {processingTaskId === item.name ? (
                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                ) : (
                                                    <Plus className="w-3 h-3" />
                                                )}
                                                업무로 등록
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </DashboardWidget>
        </div>
    );
}

interface EfficiencyCardProps {
    title: string;
    value: string;
    icon: React.ElementType;
    color: 'primary' | 'indigo' | 'blue';
    subtitle?: string;
}

function EfficiencyCard({ title, value, icon: Icon, color, subtitle }: EfficiencyCardProps) {
    const colorClasses = {
        primary: "bg-primary/5 text-primary",
        indigo: "bg-indigo-50 text-indigo-600",
        blue: "bg-blue-50 text-blue-600",
    };

    return (
        <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center justify-between mb-4">
                <div className={clsx("p-2 rounded-xl", colorClasses[color])}>
                    <Icon className="w-5 h-5" />
                </div>
                {title.includes('ROAS') && <div className="text-[10px] font-black text-green-500">+4.2%</div>}
            </div>
            <div className="text-2xl font-black text-gray-900 font-mono tracking-tighter">{value}</div>
            <div className="text-[10px] text-gray-400 mt-1 font-bold uppercase tracking-widest">{title}</div>
            <div className="mt-3 text-[10px] text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" /> {subtitle}
            </div>
        </div>
    );
}

function Clock({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
    )
}
