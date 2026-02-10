'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, CheckCircle2, AlertCircle, RefreshCcw, Activity, Terminal, ShieldAlert } from 'lucide-react';
import { getClients, createClient, deleteClient, getSystemStatus } from '@/lib/api';
import { Client } from '@/types';
import clsx from 'clsx';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';

export default function SettingsPage() {
    const [clients, setClients] = useState<Client[]>([]);
    const [status, setStatus] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'clients' | 'monitoring'>('clients');
    const [name, setName] = useState('');
    const [industry, setIndustry] = useState('');

    const fetchData = async () => {
        try {
            const clientData = await getClients();
            setClients(clientData);
            const statusData = await getSystemStatus();
            setStatus(statusData);
        } catch (error) {
            console.error('Failed to fetch settings data:', error);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleAddClient = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createClient({ name, industry, agency_id: '00000000-0000-0000-0000-000000000000' });
            setName('');
            setIndustry('');
            fetchData();
        } catch (error) {
            alert('업체 등록에 실패했습니다.');
        }
    };

    const handleDeleteClient = async (id: string) => {
        if (!confirm('정말 삭제하시겠습니까?')) return;
        try {
            await deleteClient(id);
            fetchData();
        } catch (error) {
            alert('삭제에 실패했습니다.');
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">시스템 설정</h1>
                <p className="text-gray-500">플랫폼 운영 및 업체 데이터를 관리합니다.</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-100">
                <button
                    onClick={() => setActiveTab('clients')}
                    className={clsx(
                        "pb-3 text-sm font-bold transition-all border-b-2 px-2",
                        activeTab === 'clients' ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-400 hover:text-gray-600"
                    )}
                >
                    업체 관리
                </button>
                <button
                    onClick={() => setActiveTab('monitoring')}
                    className={clsx(
                        "pb-3 text-sm font-bold transition-all border-b-2 px-2",
                        activeTab === 'monitoring' ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-400 hover:text-gray-600"
                    )}
                >
                    시스템 모니터링
                </button>
            </div>

            {activeTab === 'clients' ? (
                <div className="space-y-8">
                    {/* Onboarding Workflow Guide */}
                    <div className="bg-indigo-600 rounded-2xl p-8 text-white shadow-xl shadow-indigo-100 mb-8 relative overflow-hidden">
                        <div className="relative z-10">
                            <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
                                <Activity className="w-5 h-5" />
                                서비스 시작을 위한 3단계 가이드
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                <div className="flex gap-4 items-start">
                                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-xl shrink-0">1</div>
                                    <div>
                                        <h3 className="font-bold mb-1">업체 등록</h3>
                                        <p className="text-sm text-indigo-50/80">관리할 광고주 업체를 먼저 시스템에 등록하세요.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 items-start">
                                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-xl shrink-0">2</div>
                                    <div>
                                        <h3 className="font-bold mb-1">매체 연동</h3>
                                        <p className="text-sm text-indigo-50/80">네이버, 구글 등 광고 플랫폼 계정을 연동합니다.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 items-start">
                                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-xl shrink-0">3</div>
                                    <div>
                                        <h3 className="font-bold mb-1">분석 및 리포트</h3>
                                        <p className="text-sm text-indigo-50/80">수집된 데이터를 바탕으로 AI 리포트를 생성합니다.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="md:col-span-1">
                            <DashboardWidget title="새 업체 추가">
                                <form onSubmit={handleAddClient} className="p-6 space-y-4">
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-500 ml-1">업체명</label>
                                        <input
                                            type="text"
                                            required
                                            className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                            placeholder="예: OO치과"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-500 ml-1">업종</label>
                                        <input
                                            type="text"
                                            className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                            placeholder="예: 치과의원"
                                            value={industry}
                                            onChange={(e) => setIndustry(e.target.value)}
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        className="w-full bg-primary text-white py-3 rounded-xl font-bold text-sm hover:bg-opacity-90 transition-all shadow-md active:scale-[0.98] mt-2"
                                    >
                                        업체 등록하기
                                    </button>
                                </form>
                            </DashboardWidget>
                        </div>
                        <div className="md:col-span-2">
                            <DashboardWidget title="등록된 업체 목록">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50/50 border-b border-gray-100">
                                            <tr>
                                                <th className="px-6 py-4 text-left font-bold text-gray-500">업체명</th>
                                                <th className="px-6 py-4 text-left font-bold text-gray-500">업종</th>
                                                <th className="px-6 py-4 text-right font-bold text-gray-500">액션</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-50">
                                            {clients.map(client => (
                                                <tr key={client.id} className="hover:bg-gray-50/30 transition-colors">
                                                    <td className="px-6 py-4 font-bold text-gray-900">{client.name}</td>
                                                    <td className="px-6 py-4 text-gray-500">{client.industry || '-'}</td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button
                                                            onClick={() => handleDeleteClient(client.id)}
                                                            className="p-2 text-gray-300 hover:text-red-500 transition-colors"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                            {clients.length === 0 && (
                                                <tr>
                                                    <td colSpan={3} className="px-6 py-12 text-center text-gray-400 italic">
                                                        등록된 업체가 없습니다.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </DashboardWidget>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <DashboardWidget title="서버 상태">
                        <div className="p-6 space-y-6">
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                <div className="flex items-center gap-3">
                                    <div className={clsx(
                                        "w-3 h-3 rounded-full animate-pulse",
                                        status?.status === 'Healthy' ? "bg-emerald-500" : "bg-red-500"
                                    )} />
                                    <span className="font-bold text-gray-700">시스템 무결성</span>
                                </div>
                                <span className={clsx(
                                    "px-3 py-1 rounded-lg text-xs font-bold",
                                    status?.status === 'Healthy' ? "bg-emerald-100 text-emerald-600" : "bg-red-100 text-red-600"
                                )}>
                                    {status?.status === 'Healthy' ? '정상 운용 중' : '오류 발생'}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">DB 연결</p>
                                    <p className="text-sm font-bold text-gray-900">{status?.database || '확인 중...'}</p>
                                </div>
                                <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">스케줄러</p>
                                    <p className="text-sm font-bold text-gray-900">{status?.scheduler || '확인 중...'}</p>
                                </div>
                            </div>
                        </div>
                    </DashboardWidget>

                    <DashboardWidget title="최근 시스템 로그">
                        <div className="p-6">
                            <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs text-indigo-300 space-y-2 max-h-64 overflow-y-auto">
                                {status?.recent_logs?.map((log: any, idx: number) => (
                                    <div key={idx} className="flex gap-2">
                                        <span className="text-gray-500 text-[10px] shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                                        <span className={clsx(
                                            "font-bold shrink-0",
                                            log.level === 'INFO' ? "text-indigo-400" : "text-emerald-400"
                                        )}>{log.level}</span>
                                        <span className="text-gray-300">{log.message}</span>
                                    </div>
                                ))}
                                {!status?.recent_logs && <p>데이터를 불러오는 중...</p>}
                            </div>
                        </div>
                    </DashboardWidget>
                    <DashboardWidget title="AI 분석 모듈 (Gemini)">
                        <div className="p-6 space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-indigo-600">
                                    <ShieldAlert className="w-5 h-5" />
                                    <span className="font-bold">Gemini 2.0 Flash</span>
                                </div>
                                <span className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-bold">활성화됨</span>
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">
                                현재 플랫폼의 모든 AI 보고서 및 전략 제안은 Google Gemini API를 통해 생성됩니다. 배포 환경 변수(`GOOGLE_API_KEY`)가 설정되어 있어야 정상 작동합니다.
                            </p>
                        </div>
                    </DashboardWidget>
                </div>
            )}
        </div>
    );
}
