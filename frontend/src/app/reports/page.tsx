"use client";

import React from 'react';
import { ReportCard } from '@/components/reports/ReportCard';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { FilePlus, Settings, Filter, Search, ChevronRight } from 'lucide-react';
import { Modal } from '@/components/common/Modal';

const mockReports = [
    { title: '2026년 2월 주간 통합 마케팅 리포트', date: '2026-02-09', status: 'COMPLETED' as const, channels: ['네이버', '구글', '메타'] },
    { title: '임플란트 캠페인 성과 분석 보고서', date: '2026-02-05', status: 'COMPLETED' as const, channels: ['네이버', '유튜브'] },
    { title: '2월 월간 성과 리포트 (발송 예정)', date: '2026-03-01', status: 'SCHEDULED' as const, channels: ['전 채널'] },
    { title: '경쟁사 SOV 비교 분석 (초안)', date: '2026-02-08', status: 'DRAFT' as const, channels: ['네이버 플레이스'] },
];

const templates = [
    { name: '종합 성과 대시보드 리포트', type: 'Executive', description: 'CEO 및 의사결정권자를 위한 요약 리포트' },
    { name: '매체별 상세 분석 리포트', type: 'Channel', description: '매체별 CTR, ROAS 등 심층 지표 분석' },
    { name: '경쟁사 및 시장 분석', type: 'Strategy', description: 'SOV 및 경쟁사 키워드 점유율 분석' },
];

export default function ReportsPage() {
    const [isModalOpen, setIsModalOpen] = React.useState(false);
    const [reportName, setReportName] = React.useState('');
    const [reportType, setReportType] = React.useState('Executive');

    const handleCreateReport = () => {
        // Logic to create report (Mock for now)
        console.log('Creating report:', { reportName, reportType });
        setIsModalOpen(false);
        setReportName('');
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">리포트 센터</h1>
                    <p className="text-gray-500">통합 마케팅 성과 리포트를 생성하고 관리하세요.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-opacity-90 transition-all shadow-sm"
                >
                    <FilePlus className="h-4 w-4" /> 새 리포트 생성
                </button>
            </div>

            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="새 리포트 생성"
            >
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">리포트 제목</label>
                        <input
                            type="text"
                            className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                            placeholder="리포트 이름을 입력하세요"
                            value={reportName}
                            onChange={(e) => setReportName(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">템플릿 선택</label>
                        <select
                            className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                            value={reportType}
                            onChange={(e) => setReportType(e.target.value)}
                        >
                            {templates.map((t, i) => (
                                <option key={i} value={t.type}>{t.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="pt-4 flex gap-3">
                        <button
                            onClick={() => setIsModalOpen(false)}
                            className="flex-1 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-50"
                        >취소</button>
                        <button
                            onClick={handleCreateReport}
                            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark shadow-md"
                        >생성하기</button>
                    </div>
                </div>
            </Modal>

            {/* Template Gallery */}
            <section>
                <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">리포트 템플릿</h3>
                    <button className="text-sm font-medium text-primary hover:underline">모든 템플릿 보기</button>
                </div>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                    {templates.map((template, idx) => (
                        <div key={idx} className="group cursor-pointer rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-all hover:border-primary/20 hover:shadow-md">
                            <span className="text-[10px] font-bold text-primary uppercase tracking-wider">{template.type}</span>
                            <h4 className="mt-1 font-semibold text-gray-900">{template.name}</h4>
                            <p className="mt-2 text-xs text-gray-500 leading-relaxed">{template.description}</p>
                            <div className="mt-4 flex items-center text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                                템플릿 사용하기 <ChevronRight className="h-3 w-3 ml-1" />
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Report Management */}
            <DashboardWidget
                title="최근 생성된 리포트"
                subtitle="생성된 리포트를 확인하고 공유할 수 있습니다."
            >
                <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="리포트 검색..."
                            className="w-full rounded-lg border border-gray-200 py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none"
                        />
                    </div>
                    <div className="flex gap-2">
                        <button className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50">
                            <Filter className="h-3.5 3.5" /> 필터
                        </button>
                        <button className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50">
                            <Settings className="h-3.5 3.5" /> 자동화 설정
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
                    {mockReports.map((report, idx) => (
                        <ReportCard key={idx} {...report} />
                    ))}
                </div>
            </DashboardWidget>
        </div>
    );
}
