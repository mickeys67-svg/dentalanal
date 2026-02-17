"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, getReportTemplates, createReportTemplate, deleteReportTemplate } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import { Loader2, FileText, Plus, ChevronRight, Settings, Layout, Trash2, Edit2 } from 'lucide-react';
import Link from 'next/link';
import clsx from 'clsx';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';

export default function ReportsPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<'reports' | 'templates'>('reports');

    // 1. Fetch Reports
    const { data: reports, isLoading: isReportsLoading } = useQuery({
        queryKey: ['reports', selectedClient?.id],
        queryFn: async () => {
            if (!selectedClient) return [];
            const response = await api.get(`/api/v1/reports/${selectedClient.id}`);
            return response.data;
        },
        enabled: !!selectedClient,
        refetchInterval: (query: any) => {
            const data = query.state.data;
            if (data && data.some((r: any) => r.status === 'PENDING')) {
                return 5000; // Poll every 5s if any report is pending
            }
            return false;
        }
    });

    // 2. Fetch Templates
    const { data: templates, isLoading: isTemplatesLoading } = useQuery({
        queryKey: ['reportTemplates'],
        queryFn: getReportTemplates
    });

    const createReportMutation = useMutation({
        mutationFn: async (templateId: string) => {
            const response = await api.post('/api/v1/reports/', {
                template_id: templateId,
                client_id: selectedClient?.id,
                title: `${selectedClient?.name} 성과 정밀 분석 리포트`
            });
            return response.data;
        },
        onSuccess: () => {
            setActiveTab('reports');
            queryClient.invalidateQueries({ queryKey: ['reports'] });
        }
    });

    const deleteTemplateMutation = useMutation({
        mutationFn: deleteReportTemplate,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reportTemplates'] })
    });

    if (!selectedClient) {
        return <EmptyClientPlaceholder title="리포트를 관리할 업체를 선택해주세요" description="업체를 선택하면 과거 리포트 조회 및 신규 분석 리포트 생성이 가능합니다." />;
    }

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">성과 리포트 및 템플릿</h1>
                    <p className="text-gray-500">생성된 분석 리포트를 관리하고 커스텀 템플릿을 빌드하세요.</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-100">
                <button
                    onClick={() => setActiveTab('reports')}
                    className={clsx(
                        "px-6 py-3 text-sm font-bold transition-all border-b-2",
                        activeTab === 'reports' ? "border-primary text-primary" : "border-transparent text-gray-400 hover:text-gray-600"
                    )}
                >
                    분석 리포트 목록
                </button>
                <button
                    onClick={() => setActiveTab('templates')}
                    className={clsx(
                        "px-6 py-3 text-sm font-bold transition-all border-b-2",
                        activeTab === 'templates' ? "border-primary text-primary" : "border-transparent text-gray-400 hover:text-gray-600"
                    )}
                >
                    리포트 템플릿 설정
                </button>
            </div>

            {activeTab === 'reports' ? (
                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h2 className="text-lg font-bold text-gray-800">최근 생성된 리포트</h2>
                        <div className="flex gap-2">
                            <select
                                className="text-xs border-gray-200 rounded-lg bg-white"
                                onChange={(e) => {
                                    if (e.target.value) createReportMutation.mutate(e.target.value);
                                }}
                                disabled={createReportMutation.isPending}
                            >
                                <option value="">템플릿 선택하여 생성...</option>
                                {templates?.map((t: any) => (
                                    <option key={t.id} value={t.id}>{t.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {isReportsLoading ? (
                        <div className="flex justify-center p-12">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        </div>
                    ) : reports?.length === 0 ? (
                        <div className="bg-white border-2 border-dashed rounded-xl p-12 text-center">
                            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500 font-medium">아직 생성된 리포트가 없습니다.</p>
                            <p className="text-sm text-gray-400 mt-2">템플릿을 선택하여 첫 번째 리포트를 생성해보세요.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {reports?.map((report: any) => (
                                <div key={report.id} className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-all group">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-indigo-50 rounded-lg">
                                            <FileText className="w-6 h-6 text-primary" />
                                        </div>
                                        <span className={clsx(
                                            "text-xs font-semibold px-2 py-1 rounded-full",
                                            report.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                                        )}>
                                            {report.status === 'COMPLETED' ? '분석 완료' : '분석 중'}
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-2">{report.title}</h3>
                                    <div className="text-[10px] text-gray-400 mb-6 flex items-center justify-between">
                                        <span>생성일: {new Date(report.created_at).toLocaleDateString()}</span>
                                        <span className="bg-gray-50 px-1.5 py-0.5 rounded border">{report.template_id.substring(0, 8)}</span>
                                    </div>
                                    <Link
                                        href={`/reports/${report.id}`}
                                        className="flex items-center justify-between w-full p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm font-medium text-gray-700 transition-colors"
                                    >
                                        리포트 상세보기
                                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h2 className="text-lg font-bold text-gray-800">보유 리포트 템플릿</h2>
                        <Link
                            href="/reports/templates/builder"
                            className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-xl text-sm font-bold shadow-sm hover:bg-opacity-90"
                        >
                            <Plus className="w-4 h-4" /> 커스텀 템플릿 제작
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {templates?.map((template: any) => (
                            <div key={template.id} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm flex flex-col group">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-3 bg-indigo-50 text-primary rounded-xl">
                                            <Layout className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-gray-900">{template.name}</h3>
                                            <p className="text-xs text-gray-500">{template.description || "상세 설명 없음"}</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => {
                                                if (confirm("이 템플릿을 삭제하시겠습니까?")) deleteTemplateMutation.mutate(template.id);
                                            }}
                                            className="p-2 text-gray-300 hover:text-red-500 transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="mt-auto pt-6 border-t border-gray-50 flex items-center justify-between">
                                    <div className="flex -space-x-2">
                                        {template.config.widgets?.map((w: any, idx: number) => (
                                            <div key={idx} className="w-6 h-6 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-[8px] font-bold text-gray-400 capitalize" title={w.type}>
                                                {w.type[0]}
                                            </div>
                                        ))}
                                    </div>
                                    <button className="text-xs font-bold text-gray-400 hover:text-primary flex items-center gap-1">
                                        <Edit2 className="w-3 h-3" /> 구성 편집 (준비중)
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
