'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Trash2, ChevronRight, Building2, Mail, Pencil, Check, X as XIcon, Loader2 } from 'lucide-react';
import { deleteClient, updateClient } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import { toast } from 'sonner';

import { SetupWizard } from '@/components/setup/SetupWizard';

export default function SettingsPage() {
    const [viewMode, setViewMode] = useState<'LIST' | 'CREATE'>('LIST');
    const router = useRouter();
    const { refreshClients, clients, isLoading, setSelectedClient } = useClient();

    // 이메일 인라인 편집 상태: clientId → editValue
    const [editingEmailId, setEditingEmailId] = useState<string | null>(null);
    const [editEmailValue, setEditEmailValue] = useState('');
    const [savingEmailId, setSavingEmailId] = useState<string | null>(null);

    const handleDeleteClient = async (id: string) => {
        if (!confirm('정말 삭제하시겠습니까? 데이터가 모두 사라집니다.')) return;
        try {
            await deleteClient(id);
            await refreshClients();
        } catch {
            toast.error('삭제에 실패했습니다.');
        }
    };

    const handleStartEditEmail = (clientId: string, currentEmail: string | undefined) => {
        setEditingEmailId(clientId);
        setEditEmailValue(currentEmail || '');
    };

    const handleCancelEditEmail = () => {
        setEditingEmailId(null);
        setEditEmailValue('');
    };

    const handleSaveEmail = async (clientId: string) => {
        setSavingEmailId(clientId);
        try {
            await updateClient(clientId, { email: editEmailValue.trim() || undefined });
            await refreshClients();
            toast.success('이메일이 저장되었습니다.');
            setEditingEmailId(null);
            setEditEmailValue('');
        } catch {
            toast.error('이메일 저장에 실패했습니다.');
        } finally {
            setSavingEmailId(null);
        }
    };

    return (
        <div className="space-y-10 p-8 animate-in fade-in duration-700 max-w-7xl mx-auto">
            <div className="flex items-end justify-between border-b border-gray-100 pb-8">
                <div>
                    <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-2">프로젝트 관리 허브</h1>
                    <p className="text-lg text-gray-500 font-medium">광고주 업체 정보를 관리하고 새로운 분석 프로젝트를 시작하세요.</p>
                </div>
                {viewMode === 'LIST' ? (
                    <button
                        onClick={() => setViewMode('CREATE')}
                        className="bg-primary text-white px-8 py-4 rounded-2xl font-bold hover:shadow-xl hover:shadow-primary/20 transition-all flex items-center gap-2"
                    >
                        <Plus className="w-5 h-5" /> 새 프로젝트 시작
                    </button>
                ) : (
                    <button
                        onClick={() => setViewMode('LIST')}
                        className="text-gray-500 font-bold hover:text-gray-900 transition-all flex items-center gap-2"
                    >
                        목록으로 돌아가기
                    </button>
                )}
            </div>

            {viewMode === 'CREATE' ? (
                <div className="py-10">
                    <SetupWizard />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {clients.map(client => (
                        <div key={client.id} className="group bg-white border border-gray-100 rounded-3xl p-8 shadow-sm hover:shadow-xl hover:shadow-gray-200/50 transition-all relative overflow-hidden">
                            <div className="absolute top-2 right-2 p-2 opacity-20 group-hover:opacity-100 transition-opacity z-10">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteClient(client.id);
                                    }}
                                    className="p-3 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                                    title="프로젝트 삭제"
                                >
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="mb-6">
                                <span className="inline-block px-3 py-1 bg-indigo-50 text-primary text-[10px] font-bold rounded-full mb-3 uppercase tracking-wider">
                                    {client.industry || '기타'}
                                </span>
                                <h3 className="text-2xl font-bold text-gray-900 leading-tight">{client.name}</h3>
                            </div>

                            {/* 이메일 인라인 편집 영역 */}
                            <div className="mt-4 mb-2">
                                {editingEmailId === client.id ? (
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 flex items-center gap-1 border border-indigo-300 rounded-lg px-2 py-1 bg-indigo-50 focus-within:ring-2 focus-within:ring-indigo-300">
                                            <Mail className="w-3 h-3 text-indigo-400 shrink-0" />
                                            <input
                                                type="email"
                                                value={editEmailValue}
                                                onChange={e => setEditEmailValue(e.target.value)}
                                                onKeyDown={e => {
                                                    if (e.key === 'Enter') handleSaveEmail(client.id);
                                                    if (e.key === 'Escape') handleCancelEditEmail();
                                                }}
                                                placeholder="이메일 입력"
                                                autoFocus
                                                className="flex-1 text-xs bg-transparent outline-none text-gray-700 placeholder-gray-300"
                                            />
                                        </div>
                                        <button
                                            onClick={() => handleSaveEmail(client.id)}
                                            disabled={savingEmailId === client.id}
                                            className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
                                            title="저장"
                                        >
                                            {savingEmailId === client.id
                                                ? <Loader2 className="w-3 h-3 animate-spin" />
                                                : <Check className="w-3 h-3" />
                                            }
                                        </button>
                                        <button
                                            onClick={handleCancelEditEmail}
                                            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                            title="취소"
                                        >
                                            <XIcon className="w-3 h-3" />
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => handleStartEditEmail(client.id, (client as any).email)}
                                        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-indigo-600 transition-colors group/email"
                                        title="리포트 수신 이메일 편집"
                                    >
                                        <Mail className="w-3 h-3" />
                                        <span className={(client as any).email ? 'text-gray-600 font-medium' : 'italic'}>
                                            {(client as any).email || '이메일 미설정'}
                                        </span>
                                        <Pencil className="w-3 h-3 opacity-0 group-hover/email:opacity-100 transition-opacity" />
                                    </button>
                                )}
                            </div>

                            <div className="flex items-center justify-between mt-4 pt-6 border-t border-gray-50">
                                <div className="text-xs text-gray-400 space-y-1">
                                    <div className="flex items-center gap-1">
                                        <span className="font-bold text-gray-900">3개의 타겟</span> 연동됨
                                    </div>
                                    {client.created_at && (
                                        <div className="text-[10px] text-gray-300">
                                            등록일: {new Date(client.created_at).toLocaleDateString('ko-KR')}
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={() => {
                                        setSelectedClient(client);
                                        router.push('/dashboard');
                                    }}
                                    className="text-primary font-bold text-sm flex items-center gap-1 group-hover:gap-2 transition-all"
                                >
                                    데이터 보기 <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}

                    {clients.length === 0 && !isLoading && (
                        <div className="col-span-full py-20 text-center bg-gray-50 rounded-3xl border-2 border-dashed border-gray-100">
                            <Building2 className="w-16 h-16 text-gray-200 mx-auto mb-4" />
                            <p className="text-gray-400 font-medium">아직 등록된 프로젝트가 없습니다.<br />첫 번째 분석을 시작해보세요!</p>
                            <button
                                onClick={() => setViewMode('CREATE')}
                                className="mt-6 text-primary font-bold hover:underline"
                            >
                                새 프로젝트 등록하기
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
