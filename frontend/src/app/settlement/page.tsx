"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettlements, generateSettlement, updateSettlementStatus } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import {
    CreditCard, Download, Receipt, AlertCircle,
    CheckCircle2, Clock, Calendar, Plus,
    Loader2, ChevronRight, Calculator
} from 'lucide-react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import clsx from 'clsx';
import { Settlement } from '@/types';

export default function SettlementPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();
    const [isGenerating, setIsGenerating] = useState(false);

    const { data: settlements, isLoading } = useQuery<Settlement[]>({
        queryKey: ['settlements', selectedClient?.id],
        queryFn: () => getSettlements(selectedClient!.id),
        enabled: !!selectedClient
    });

    const generateMutation = useMutation({
        mutationFn: (vars: { year: number, month: number }) =>
            generateSettlement(selectedClient!.id, vars.year, vars.month),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settlements', selectedClient?.id] });
            setIsGenerating(false);
            alert('정산 데이터가 생성되었습니다.');
        },
        onError: (err: any) => {
            alert(err?.response?.data?.detail || "정산 데이터 생성 실패");
            setIsGenerating(false);
        }
    });

    const statusMutation = useMutation({
        mutationFn: (vars: { id: string, status: string }) =>
            updateSettlementStatus(vars.id, vars.status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settlements', selectedClient?.id] });
            alert('상태가 변경되었습니다.');
        }
    });

    const handleGenerate = () => {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth(); // Previous month
        const targetMonth = month === 0 ? 12 : month;
        const targetYear = month === 0 ? year - 1 : year;

        setIsGenerating(true);
        generateMutation.mutate({ year: targetYear, month: targetMonth });
    };

    if (!selectedClient) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] text-gray-400">
                <Calculator className="w-16 h-16 mb-4 opacity-10" />
                <p>업체를 선택하면 정산 내역을 확인할 수 있습니다.</p>
            </div>
        );
    }

    const pendingAmount = settlements?.filter(s => s.status === 'PENDING').reduce((acc, s) => acc + s.total_amount, 0) || 0;
    const lastMonthSpend = settlements?.[0]?.total_spend || 0;

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-700">
            {/* ... Rest of JSX remains basically same but using typed s */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">정산 및 대금 관리</h1>
                    <p className="text-sm text-gray-500">광고 집행 데이터 기반 자동 정산 및 청구 내역입니다.</p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    className="flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-xl font-bold shadow-lg shadow-indigo-100 hover:bg-opacity-90 transition-all disabled:opacity-50"
                >
                    {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    지난 달 정산 생성 (실시간)
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2 bg-indigo-50 text-primary rounded-lg text-xs font-bold uppercase tracking-wider">미결제 합계</div>
                        <AlertCircle className="w-4 h-4 text-amber-400" />
                    </div>
                    <div className="text-3xl font-black text-gray-900 font-mono">
                        ₩ {pendingAmount.toLocaleString()}
                    </div>
                    <p className="text-[10px] text-gray-400 mt-2">입금 대기 중인 정산 건수: {settlements?.filter(s => s.status === 'PENDING').length || 0}건</p>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm text-gray-900">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2 bg-green-50 text-green-600 rounded-lg text-xs font-bold uppercase tracking-wider">최근 광고비 집행</div>
                        <Calendar className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="text-3xl font-black font-mono tracking-tighter">
                        ₩ {lastMonthSpend.toLocaleString()}
                    </div>
                    <p className="text-[10px] text-gray-400 mt-2">대상 기간: {settlements?.[0]?.period || '없음'}</p>
                </div>

                <div className="bg-indigo-600 p-6 rounded-3xl shadow-xl shadow-indigo-100 text-white flex flex-col justify-between">
                    <div>
                        <div className="text-xs font-bold text-indigo-200 uppercase tracking-widest mb-1">PRO SERVICE</div>
                        <h3 className="font-bold">자동 세금계산서 발행</h3>
                    </div>
                    <div className="flex items-center justify-between">
                        <p className="text-[10px] text-indigo-100 leading-tight">정산 완료 시 이메일로<br />영수증이 자동 발송됩니다.</p>
                        <Receipt className="w-8 h-8 opacity-20" />
                    </div>
                </div>
            </div>

            {/* Settlement List */}
            <DashboardWidget title="정산 내역 리스트" subtitle="월간 단위로 집계된 모든 대금 청구 내역입니다.">
                {isLoading ? (
                    <div className="py-20 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
                ) : !settlements || settlements.length === 0 ? (
                    <div className="py-20 text-center text-gray-400 font-medium">
                        정산 내역이 없습니다. (지난 달 정산을 생성해주세요)
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50">
                                    <th className="py-4 px-2">정산 기간</th>
                                    <th className="py-4">상태</th>
                                    <th className="py-4">집행 광고비</th>
                                    <th className="py-4">대행 수수료 (+VAT)</th>
                                    <th className="py-4">총 청구 금액</th>
                                    <th className="py-4">마감일 / 처리일</th>
                                    <th className="py-4 text-right">관리</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {settlements.map((s: Settlement) => (
                                    <tr key={s.id} className="hover:bg-gray-50/50 transition-all group">
                                        <td className="py-6 px-2">
                                            <div className="font-bold text-gray-900">{s.period}</div>
                                            <div className="text-[10px] text-gray-400">ID: {s.id.substring(0, 8)}...</div>
                                        </td>
                                        <td className="py-6">
                                            <span className={clsx(
                                                "px-3 py-1 rounded-full text-[10px] font-black tracking-tighter uppercase",
                                                s.status === 'PAID' ? "bg-green-100 text-green-700" :
                                                    s.status === 'PENDING' ? "bg-amber-100 text-amber-700" :
                                                        "bg-gray-100 text-gray-400"
                                            )}>
                                                {s.status}
                                            </span>
                                        </td>
                                        <td className="py-6 font-mono text-xs text-gray-500">₩ {s.total_spend.toLocaleString()}</td>
                                        <td className="py-6 font-mono text-xs text-gray-500">₩ {s.fee_amount.toLocaleString()} (+{(s.tax_amount).toLocaleString()})</td>
                                        <td className="py-6 font-black text-sm text-gray-900 font-mono">₩ {s.total_amount.toLocaleString()}</td>
                                        <td className="py-6 text-xs text-gray-400">
                                            {s.paid_at ? (
                                                <div className="flex items-center gap-1 text-green-600 font-bold">
                                                    <CheckCircle2 className="w-3 h-3" /> {new Date(s.paid_at).toLocaleDateString()}
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" /> {s.due_date ? new Date(s.due_date).toLocaleDateString() : '-'}
                                                </div>
                                            )}
                                        </td>
                                        <td className="py-6 text-right">
                                            <div className="flex justify-end gap-2">
                                                {s.status === 'PENDING' && (
                                                    <button
                                                        onClick={() => statusMutation.mutate({ id: s.id, status: 'PAID' })}
                                                        className="px-3 py-1.5 bg-success text-white text-[10px] font-bold rounded-lg hover:bg-opacity-90 transition-all"
                                                    >
                                                        입금 확인
                                                    </button>
                                                )}
                                                <button className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 transition-all">
                                                    <Download className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </DashboardWidget>
        </div>
    );
}
