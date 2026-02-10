"use client";

import React from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { useClient } from '@/components/providers/ClientProvider';
import { createClient, deleteClient } from '@/lib/api';
import { Plus, Trash2 } from 'lucide-react';

export default function SettingsPage() {
    const { clients, refreshClients } = useClient();
    const [newClientName, setNewClientName] = React.useState('');
    const [newClientIndustry, setNewClientIndustry] = React.useState('치과');

    const handleAddClient = async () => {
        if (!newClientName) return;
        try {
            await createClient({
                name: newClientName,
                industry: newClientIndustry,
                agency_id: '00000000-0000-0000-0000-000000000000' // Default agency ID
            });
            setNewClientName('');
            await refreshClients();
        } catch (error) {
            console.error('Failed to add client:', error);
        }
    };

    const handleDeleteClient = async (id: string) => {
        if (!confirm('정말 이 업체를 삭제하시겠습니까?')) return;
        try {
            await deleteClient(id);
            await refreshClients();
        } catch (error) {
            console.error('Failed to delete client:', error);
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">설정 (Settings)</h1>
                    <p className="text-gray-500">계정 및 플랫폼 환경 설정을 관리합니다.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <DashboardWidget title="업체(Client) 관리">
                    <div className="p-4 space-y-6">
                        <div className="space-y-4">
                            <h4 className="text-sm font-bold text-gray-700">새 업체 등록</h4>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="업체명 (예: OO 치과)"
                                    value={newClientName}
                                    onChange={(e) => setNewClientName(e.target.value)}
                                    className="flex-1 text-sm border-gray-200 rounded-lg focus:ring-primary focus:border-primary"
                                />
                                <select
                                    value={newClientIndustry}
                                    onChange={(e) => setNewClientIndustry(e.target.value)}
                                    className="text-sm border-gray-200 rounded-lg focus:ring-primary focus:border-primary w-32"
                                >
                                    <option value="치과">치과</option>
                                    <option value="의원">의원</option>
                                    <option value="한의원">한의원</option>
                                    <option value="기타">기타</option>
                                </select>
                                <button
                                    onClick={handleAddClient}
                                    className="bg-primary text-white p-2 rounded-lg hover:bg-primary-dark transition-colors"
                                >
                                    <Plus className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h4 className="text-sm font-bold text-gray-700">등록된 업체 목록</h4>
                            <div className="border border-gray-100 rounded-xl overflow-hidden">
                                {clients.length === 0 ? (
                                    <div className="p-8 text-center text-sm text-gray-400 italic">등록된 업체가 없습니다.</div>
                                ) : (
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-bold text-gray-500">업체명</th>
                                                <th className="px-4 py-2 text-left font-bold text-gray-500">업종</th>
                                                <th className="px-4 py-2 text-right font-bold text-gray-500">관리</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-50">
                                            {clients.map(client => (
                                                <tr key={client.id} className="hover:bg-gray-50/50">
                                                    <td className="px-4 py-3 font-semibold text-gray-900">{client.name}</td>
                                                    <td className="px-4 py-3 text-gray-500">{client.industry}</td>
                                                    <td className="px-4 py-3 text-right">
                                                        <button
                                                            onClick={() => handleDeleteClient(client.id)}
                                                            className="text-red-400 hover:text-red-500 p-1"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                </DashboardWidget>

                <div className="space-y-6">
                    <DashboardWidget title="데이터베이스 상태">
                        <div className="p-4 space-y-3">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-500">현재 DB 엔진:</span>
                                <span className="font-bold text-success">Cloud SQL & SQLite</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-500">스키마 초기화:</span>
                                <span className="font-bold text-success">정상</span>
                            </div>
                            <p className="text-[10px] text-gray-400 mt-4 italic">* GCP 환경에서는 Cloud SQL을 기본으로 하며 로컬 개발 시에는 SQLite를 사용합니다.</p>
                        </div>
                    </DashboardWidget>
                    <DashboardWidget title="시스템 알림 설정">
                        <div className="p-8 text-center text-gray-400">
                            <p className="text-sm">메일 및 슬랙 알림 서비스 준비 중</p>
                        </div>
                    </DashboardWidget>
                </div>
            </div>
        </div>
    );
}
