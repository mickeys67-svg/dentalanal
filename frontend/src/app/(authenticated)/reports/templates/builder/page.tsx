"use client";

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createReportTemplate } from '@/lib/api';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft, Save, Plus, Trash2, GripVertical,
    BarChart3, PieChart, Activity, Brain, LayoutGrid
} from 'lucide-react';
import Link from 'next/link';

const AVAILABLE_WIDGETS = [
    { type: 'KPI_GROUP', name: '성과 요약 (Spend, ROI 등)', icon: Activity, description: '핵심 지표들을 한눈에 보여줍니다.' },
    { type: 'FUNNEL', name: '전환 퍼널 분석', icon: PieChart, description: '유입부터 전환까지의 단계를 분석합니다.' },
    { type: 'LINE_CHART', name: '성과 추이 차트', icon: BarChart3, description: '날짜별 지표 변화를 그래프로 매핑합니다.' },
    { type: 'BENCHMARK', name: '업종 평균 비교', icon: LayoutGrid, description: '내 성과와 업종 평균 데이터를 비교합니다.' },
    { type: 'SOV', name: '노출 점유율 (SOV)', icon: Activity, description: '경쟁사 대비 우리 병원의 노출 비중 분석.' },
    { type: 'COMPETITORS', name: '경쟁사 정밀 분석', icon: LayoutGrid, description: '상위 노출되는 경쟁사 명단 및 점유율.' },
    { type: 'RANKINGS', name: '실시간 순위 현황', icon: BarChart3, description: '주요 키워드별 현재 노출 순위 리스트.' },
    { type: 'AI_DIAGNOSIS', name: 'Gemini AI 성과 진단', icon: Brain, description: 'AI가 제공하는 맞춤형 인사이트와 조언.' },
];

export default function TemplateBuilderPage() {
    const router = useRouter();
    const queryClient = useQueryClient();
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [selectedWidgets, setSelectedWidgets] = useState<any[]>([]);

    const createMutation = useMutation({
        mutationFn: createReportTemplate,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reportTemplates'] });
            router.push('/reports');
        }
    });

    const addWidget = (widget: any) => {
        const newWidget = {
            id: `widget_${Date.now()}`,
            type: widget.type,
            title: widget.name,
            config: {}
        };
        setSelectedWidgets([...selectedWidgets, newWidget]);
    };

    const removeWidget = (id: string) => {
        setSelectedWidgets(selectedWidgets.filter(w => w.id !== id));
    };

    const handleSave = () => {
        if (!name) {
            alert('템플릿 이름을 입력해주세요.');
            return;
        }
        if (selectedWidgets.length === 0) {
            alert('최소 하나 이상의 위젯을 추가해주세요.');
            return;
        }

        createMutation.mutate({
            name,
            description,
            config: {
                layout: 'grid',
                widgets: selectedWidgets
            }
        });
    };

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in slide-in-from-bottom duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/reports" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5 text-gray-500" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">리포트 템플릿 제작</h1>
                        <p className="text-sm text-gray-500">원하는 위젯을 조합하여 병원만의 리포트 형식을 만드세요.</p>
                    </div>
                </div>
                <button
                    onClick={handleSave}
                    disabled={createMutation.isPending}
                    className="flex items-center gap-2 bg-primary text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-indigo-100 hover:bg-opacity-90 transition-all"
                >
                    {createMutation.isPending ? <Activity className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    템플릿 저장하기
                </button>
            </div>

            <div className="grid grid-cols-12 gap-8">
                {/* Sidebar: Widget Library */}
                <div className="col-span-12 lg:col-span-4 space-y-6">
                    <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm overflow-hidden">
                        <h3 className="font-bold text-gray-900 mb-6 flex items-center gap-2">
                            <Plus className="w-4 h-4 text-primary" /> 위젯 라이브러리
                        </h3>
                        <div className="space-y-3">
                            {AVAILABLE_WIDGETS.map((w) => (
                                <button
                                    key={w.type}
                                    onClick={() => addWidget(w)}
                                    className="w-full flex items-start gap-4 p-4 rounded-2xl hover:bg-indigo-50 hover:border-indigo-100 border border-transparent transition-all group text-left"
                                >
                                    <div className="p-3 bg-gray-50 text-gray-400 group-hover:bg-white group-hover:text-primary rounded-xl transition-all">
                                        <w.icon className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-bold text-gray-700 group-hover:text-primary">{w.name}</h4>
                                        <p className="text-[11px] text-gray-400 mt-0.5">{w.description}</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="bg-indigo-50/50 rounded-3xl p-6 border border-indigo-100/30">
                        <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-4">템플릿 기본 정보</h4>
                        <div className="space-y-4">
                            <div>
                                <label className="text-[11px] font-bold text-gray-400 ml-1">템플릿 이름</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="예: 월간 성과 상세 분석"
                                    className="w-full mt-1 px-4 py-3 rounded-xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-primary text-sm font-medium"
                                />
                            </div>
                            <div>
                                <label className="text-[11px] font-bold text-gray-400 ml-1">설명 (선택)</label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="템플릿에 대한 설명을 입력하세요."
                                    rows={3}
                                    className="w-full mt-1 px-4 py-3 rounded-xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-primary text-sm font-medium resize-none"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Canvas: selected widgets */}
                <div className="col-span-12 lg:col-span-8 space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h2 className="text-lg font-bold text-gray-900">리포트 레이아웃 프리뷰</h2>
                        <span className="text-[10px] font-bold text-gray-400 uppercase">총 {selectedWidgets.length}개 위젯 배치됨</span>
                    </div>

                    {selectedWidgets.length === 0 ? (
                        <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-[2.5rem] py-32 flex flex-col items-center justify-center text-gray-400 animate-pulse">
                            <LayoutGrid className="w-12 h-12 mb-4 opacity-10" />
                            <p className="text-sm font-medium">왼쪽 라이브러리에서 위젯을 클릭하여 추가하세요.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {selectedWidgets.map((sw, idx) => (
                                <div key={sw.id} className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm flex items-center gap-6 group hover:border-primary/30 transition-all">
                                    <div className="text-gray-300 group-hover:text-primary transition-colors cursor-grab active:cursor-grabbing">
                                        <GripVertical className="w-5 h-5" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[10px] font-black text-indigo-400">0{idx + 1}</span>
                                            <h4 className="text-sm font-bold text-gray-800">{sw.title}</h4>
                                        </div>
                                        <div className="h-12 bg-gray-50 rounded-xl flex items-center px-4">
                                            <span className="text-[10px] font-bold text-gray-300 uppercase letter tracking-tighter">Widget Type: {sw.type} Preview Area</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => removeWidget(sw.id)}
                                        className="p-3 rounded-2xl bg-gray-50 text-gray-300 hover:bg-red-50 hover:text-red-500 transition-all"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
