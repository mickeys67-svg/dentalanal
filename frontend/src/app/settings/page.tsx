'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, CheckCircle2, AlertCircle, RefreshCcw, Activity, Terminal, ShieldAlert } from 'lucide-react';
import { getClients, createClient, deleteClient, getSystemStatus } from '@/lib/api';
import { Client } from '@/types';
import clsx from 'clsx';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { useClient } from '@/components/providers/ClientProvider';
import { useAuth } from '@/components/providers/AuthProvider';

export default function SettingsPage() {
    const [name, setName] = useState('');
    const [industry, setIndustry] = useState('');

    const { refreshClients, clients, isLoading } = useClient();
    const { user } = useAuth();

    const handleAddClient = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createClient({
                name,
                industry,
                agency_id: user?.agency_id || '00000000-0000-0000-0000-000000000000'
            });
            setName('');
            setIndustry('');
            await refreshClients();
        } catch (error) {
            alert('업체 등록에 실패했습니다.');
        }
    };

    const handleDeleteClient = async (id: string) => {
        if (!confirm('정말 삭제하시겠습니까?')) return;
        try {
            await deleteClient(id);
            await refreshClients();
        } catch (error) {
            alert('삭제에 실패했습니다.');
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">업체 데이터 관리</h1>
                <p className="text-gray-500">광고주 업체 정보를 등록 및 편집합니다.</p>
            </div>


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
                                    <label htmlFor="client-name" className="text-xs font-bold text-gray-500 ml-1">업체명</label>
                                    <input
                                        id="client-name"
                                        name="name"
                                        type="text"
                                        required
                                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                        placeholder="예: OO치과"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label htmlFor="client-industry" className="text-xs font-bold text-gray-500 ml-1">업종</label>
                                    <select
                                        id="client-industry"
                                        name="industry"
                                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all appearance-none cursor-pointer"
                                        value={industry}
                                        onChange={(e) => setIndustry(e.target.value)}
                                        required
                                    >
                                        <option value="" disabled>업종을 선택하세요</option>
                                        <option value="치과의원">치과의원</option>
                                        <option value="성형외과">성형외과</option>
                                        <option value="피부과">피부과</option>
                                        <option value="안과">안과</option>
                                        <option value="정형외과">정형외과</option>
                                        <option value="한의원">한의원</option>
                                        <option value="내과">내과</option>
                                        <option value="기타">기타</option>
                                    </select>
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
        </div>
    );
}
