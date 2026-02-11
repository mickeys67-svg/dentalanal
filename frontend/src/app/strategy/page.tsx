"use client";

import React, { useState, useEffect } from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import {
    Lightbulb,
    Target,
    Calculator,
    TrendingUp,
    CheckCircle,
    ChevronRight,
    Sparkles,
    Cpu,
    Plus,
    Save
} from 'lucide-react';
import clsx from 'clsx';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSWOT, saveSWOT, getStrategyGoals, createStrategyGoal, generateAdCopy } from '@/lib/api';
import { SWOTData, StrategyGoal } from '@/types';
import { Notification, NotificationType } from '@/components/common/Notification';
import { Modal } from '@/components/common/Modal';
import { useClient } from '@/components/providers/ClientProvider';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';


export default function StrategyPage() {
    const queryClient = useQueryClient();
    const { selectedClient } = useClient();

    if (!selectedClient) {
        return <EmptyClientPlaceholder title="전략을 수립할 업체를 선택해주세요" description="업체를 선택하면 SWOT 분석 및 AI 타겟팅 전략 수립이 가능합니다." />;
    }

    const [swotState, setSwotState] = useState<SWOTData>({
        strengths: [], weaknesses: [], opportunities: [], threats: []
    });

    const [notification, setNotification] = useState<{ message: string; type: NotificationType } | null>(null);

    // Modal States
    const [isSwotModalOpen, setIsSwotModalOpen] = useState(false);
    const [currentSwotType, setCurrentSwotType] = useState<keyof SWOTData | null>(null);
    const [newSwotValue, setNewSwotValue] = useState('');

    const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
    const [newGoalTitle, setNewGoalTitle] = useState('');

    // AI State
    const [aiCopy, setAiCopy] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    // 1. Data Fetching
    const currentClientId = selectedClient?.id;

    const { data: swotData, isLoading: isSwotLoading } = useQuery({
        queryKey: ['swot', currentClientId],
        queryFn: () => getSWOT(currentClientId!),
        enabled: !!currentClientId
    });

    useEffect(() => {
        if (swotData) {
            setSwotState({
                strengths: swotData.strengths || [],
                weaknesses: swotData.weaknesses || [],
                opportunities: swotData.opportunities || [],
                threats: swotData.threats || []
            });
        }
    }, [swotData]);

    const { data: goals, isLoading: isGoalsLoading } = useQuery({
        queryKey: ['goals', currentClientId],
        queryFn: () => getStrategyGoals(currentClientId!),
        enabled: !!currentClientId
    });

    // 2. Mutations
    const swotMutation = useMutation({
        mutationFn: (data: SWOTData) => saveSWOT(currentClientId!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['swot'] });
            setNotification({ message: "SWOT 분석이 성공적으로 저장되었습니다.", type: 'SUCCESS' });
        },
        onError: () => {
            setNotification({ message: "저장 중 오류가 발생했습니다.", type: 'ERROR' });
        }
    });

    const goalMutation = useMutation({
        mutationFn: (data: Partial<StrategyGoal>) => createStrategyGoal(currentClientId!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
            setNotification({ message: "목표가 등록되었습니다.", type: 'SUCCESS' });
            setIsGoalModalOpen(false);
            setNewGoalTitle('');
        }
    });

    // 3. Handlers
    const handleSaveSwot = () => {
        swotMutation.mutate(swotState);
    };

    const openSwotModal = (type: keyof SWOTData) => {
        setCurrentSwotType(type);
        setIsSwotModalOpen(true);
    };

    const handleAddSwotItem = () => {
        if (currentSwotType && newSwotValue) {
            setSwotState(prev => ({
                ...prev,
                [currentSwotType]: [...prev[currentSwotType], newSwotValue]
            }));
            setNewSwotValue('');
            setIsSwotModalOpen(false);
        }
    };

    const handleAddGoal = () => {
        if (!newGoalTitle) return;
        goalMutation.mutate({
            title: newGoalTitle,
            smart_m: '진행 중'
        });
    };

    const handleGenerateCopy = async () => {
        setIsGenerating(true);
        try {
            const result = await generateAdCopy({
                swot_data: swotState,
                target_audience: "현재 지역 거주 잠재 고객",
                key_proposition: "전문적이며 과잉 진료 없는 정직한 진료"
            });
            if (result && result.length > 0) {
                setAiCopy(result[0].content);
                setNotification({ message: "AI 전략 제안이 생성되었습니다.", type: 'SUCCESS' });
            }
        } catch (error) {
            console.error(error);
            setNotification({ message: "AI 생산 중 오류가 발생했습니다.", type: 'ERROR' });
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">AI 전략 워크스페이스</h1>
                    <p className="text-gray-500">데이터와 AI를 활용하여 최적의 마케팅 전략을 수립하세요.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleSaveSwot}
                        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all"
                    >
                        <Save className="h-4 w-4" /> 전략 저장
                    </button>
                    <button
                        onClick={handleGenerateCopy}
                        disabled={isGenerating}
                        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-opacity-90 shadow-sm transition-all disabled:opacity-50"
                    >
                        <Sparkles className="h-4 w-4" /> {isGenerating ? "영감 한 스푼..." : "AI 전략 생성"}
                    </button>
                </div>
            </div>

            {/* AI Recommendation Section */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-700 p-8 text-white shadow-lg">
                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="max-w-2xl">
                        <div className="flex items-center gap-2 text-indigo-100 text-sm font-semibold mb-4">
                            <Cpu className="h-5 w-5" />
                            <span>Gemini AI 분석 리포트</span>
                        </div>
                        <h2 className="text-2xl font-bold mb-4">현재 캠페인 최적화 전략 제안</h2>
                        <p className="text-indigo-50 leading-relaxed">
                            {isGenerating ? "Gemini AI가 데이터를 기반으로 최적의 전략을 구성하고 있습니다..." :
                                aiCopy || "최근 데이터를 분석한 결과와 수립된 SWOT 분석을 바탕으로 AI가 구체적인 매체 믹스 및 광고 타겟팅 전략을 제안할 준비가 되었습니다. 'AI 전략 생성' 버튼을 클릭해 주세요."}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* SWOT Matrix */}
                <DashboardWidget title="SWOT 분석" className="lg:col-span-2">
                    <div className="grid grid-cols-2 gap-4">
                        {[
                            { key: 'strengths', label: 'Strengths (강점)', bgColor: 'bg-green-50', borderColor: 'border-green-100', textColor: 'text-green-700', listColor: 'text-green-800' },
                            { key: 'weaknesses', label: 'Weaknesses (약점)', bgColor: 'bg-red-50', borderColor: 'border-red-100', textColor: 'text-red-700', listColor: 'text-red-800' },
                            { key: 'opportunities', label: 'Opportunities (기회)', bgColor: 'bg-blue-50', borderColor: 'border-blue-100', textColor: 'text-blue-700', listColor: 'text-blue-800' },
                            { key: 'threats', label: 'Threats (위협)', bgColor: 'bg-amber-50', borderColor: 'border-amber-100', textColor: 'text-amber-700', listColor: 'text-amber-800' }
                        ].map((box) => (
                            <div key={box.key} className={clsx("rounded-xl p-4 border relative group", box.bgColor, box.borderColor)}>
                                <h4 className={clsx("text-xs font-bold uppercase mb-3", box.textColor)}>{box.label}</h4>
                                <ul className={clsx("text-xs space-y-2", box.listColor)}>
                                    {(swotState[box.key as keyof SWOTData] || []).map((item: string, i: number) => (
                                        <li key={i} className="flex items-center gap-2"><CheckCircle className="h-3 w-3" /> {item}</li>
                                    ))}
                                    {(!swotState[box.key as keyof SWOTData] || swotState[box.key as keyof SWOTData].length === 0) && (
                                        <li className="text-gray-400 italic">내용을 추가해 주세요.</li>
                                    )}
                                </ul>
                                <button
                                    onClick={() => openSwotModal(box.key as keyof SWOTData)}
                                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-full bg-white/50 hover:bg-white text-gray-500"
                                >
                                    <Plus className="h-3 w-3" />
                                </button>
                            </div>
                        ))}
                    </div>
                </DashboardWidget>

                {/* SMART Goals */}
                <DashboardWidget title="SMART 목표 현황">
                    <div className="space-y-6">
                        {isGoalsLoading ? (
                            <div className="animate-pulse space-y-4">
                                <div className="h-4 bg-gray-100 rounded w-3/4"></div>
                                <div className="h-4 bg-gray-100 rounded w-full"></div>
                            </div>
                        ) : goals && goals.length > 0 ? (
                            goals.map((goal: StrategyGoal, idx: number) => (
                                <div key={idx} className="space-y-2">
                                    <div className="flex justify-between text-xs font-medium">
                                        <span className="text-gray-600 font-bold uppercase tracking-wider">{goal.title}</span>
                                        <span className="text-primary">{goal.smart_m || '진행 중'}</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-primary" style={{ width: '60%' }}></div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-6">
                                <Target className="h-8 w-8 text-gray-200 mx-auto mb-2" />
                                <p className="text-xs text-gray-400">설정된 목표가 없습니다.</p>
                            </div>
                        )}
                        <button
                            onClick={() => setIsGoalModalOpen(true)}
                            className="w-full mt-4 flex items-center justify-center gap-2 rounded-lg border border-gray-100 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-all cursor-pointer"
                        >
                            새 목표 설정 <ChevronRight className="h-4 w-4" />
                        </button>
                    </div>
                </DashboardWidget>
            </div>

            {/* Modals */}
            <Modal
                isOpen={isSwotModalOpen}
                onClose={() => setIsSwotModalOpen(false)}
                title={`${currentSwotType === 'strengths' ? '강점' : currentSwotType === 'weaknesses' ? '약점' : currentSwotType === 'opportunities' ? '기회' : '위협'} 항목 추가`}
            >
                <div className="space-y-4">
                    <textarea
                        className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary h-24"
                        placeholder="내용을 입력하세요"
                        value={newSwotValue}
                        onChange={(e) => setNewSwotValue(e.target.value)}
                    />
                    <div className="flex gap-3">
                        <button onClick={() => setIsSwotModalOpen(false)} className="flex-1 py-2 border rounded-lg text-sm font-medium">취소</button>
                        <button onClick={handleAddSwotItem} className="flex-1 py-2 bg-primary text-white rounded-lg text-sm font-medium">추가하기</button>
                    </div>
                </div>
            </Modal>

            <Modal
                isOpen={isGoalModalOpen}
                onClose={() => setIsGoalModalOpen(false)}
                title="새 목표 설정"
            >
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">목표 설명</label>
                        <input
                            type="text"
                            className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                            placeholder="예: 네이버 플레이스 순위 상승"
                            value={newGoalTitle}
                            onChange={(e) => setNewGoalTitle(e.target.value)}
                        />
                    </div>
                    <div className="pt-4 flex gap-3">
                        <button onClick={() => setIsGoalModalOpen(false)} className="flex-1 py-2 border rounded-lg text-sm font-medium text-gray-600">취소</button>
                        <button onClick={handleAddGoal} className="flex-1 py-2 bg-primary text-white rounded-lg text-sm font-medium">등록하기</button>
                    </div>
                </div>
            </Modal>

            {notification && (
                <Notification
                    message={notification.message}
                    type={notification.type}
                    onClose={() => setNotification(null)}
                />
            )}
        </div>
    );
}
