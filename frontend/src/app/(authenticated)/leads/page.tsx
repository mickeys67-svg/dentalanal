'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Users, TrendingUp, UserPlus, DollarSign, Loader2, Plus, Trash2, Filter, BarChart3, X } from 'lucide-react';
import { useClient } from '@/components/providers/ClientProvider';
import { getLeads, getLeadSummary, createLead, deleteLead, Lead, LeadSummary } from '@/lib/api';
import { toast } from 'sonner';

// ── 채널 설정 ────────────────────────────────────────────────────────────────
const CHANNELS = [
    { value: 'paid', label: '유료 광고', color: '#6366f1' },
    { value: 'organic', label: '자연 검색', color: '#10b981' },
    { value: 'social', label: 'SNS', color: '#f59e0b' },
    { value: 'referral', label: '추천/소개', color: '#3b82f6' },
    { value: 'direct', label: '직접 유입', color: '#8b5cf6' },
    { value: 'unknown', label: '기타', color: '#9ca3af' },
];

const channelLabel = (ch: string | null) => CHANNELS.find(c => c.value === ch)?.label ?? ch ?? '미분류';
const channelColor = (ch: string | null) => CHANNELS.find(c => c.value === ch)?.color ?? '#9ca3af';

// ── KPI 카드 ──────────────────────────────────────────────────────────────────
function KpiCard({ icon, label, value, sub, color }: {
    icon: React.ReactNode;
    label: string;
    value: string;
    sub?: string;
    color: string;
}) {
    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center`} style={{ background: color + '18' }}>
                    <span style={{ color }}>{icon}</span>
                </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
            {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
        </div>
    );
}

// ── 채널 바 ───────────────────────────────────────────────────────────────────
function ChannelBar({ by_channel, total }: { by_channel: Record<string, number>; total: number }) {
    if (total === 0) return null;
    const sorted = Object.entries(by_channel).sort((a, b) => b[1] - a[1]);
    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-500" /> 유입 채널 분포
            </h3>
            <div className="space-y-3">
                {sorted.map(([ch, cnt]) => {
                    const pct = Math.round(cnt / total * 100);
                    return (
                        <div key={ch}>
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-600 font-medium">{channelLabel(ch)}</span>
                                <span className="text-gray-400">{cnt}명 ({pct}%)</span>
                            </div>
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-500"
                                    style={{ width: `${pct}%`, background: channelColor(ch) }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// ── 리드 등록 모달 ────────────────────────────────────────────────────────────
function AddLeadModal({ clientId, onClose, onCreated }: {
    clientId: string;
    onClose: () => void;
    onCreated: () => void;
}) {
    const [form, setForm] = useState({ name: '', contact: '', channel: 'paid', first_visit_date: '' });
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            await createLead({
                client_id: clientId,
                name: form.name || undefined,
                contact: form.contact || undefined,
                channel: form.channel,
                first_visit_date: form.first_visit_date || undefined,
            });
            toast.success('리드가 등록되었습니다.');
            onCreated();
        } catch {
            toast.error('등록에 실패했습니다.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md mx-4 p-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-gray-900">리드 등록</h2>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 mb-1.5">이름 (선택)</label>
                        <input
                            type="text"
                            value={form.name}
                            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                            placeholder="홍길동"
                            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 mb-1.5">연락처 (선택)</label>
                        <input
                            type="text"
                            value={form.contact}
                            onChange={e => setForm(f => ({ ...f, contact: e.target.value }))}
                            placeholder="010-0000-0000"
                            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 mb-1.5">유입 채널</label>
                        <select
                            value={form.channel}
                            onChange={e => setForm(f => ({ ...f, channel: e.target.value }))}
                            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
                        >
                            {CHANNELS.map(c => (
                                <option key={c.value} value={c.value}>{c.label}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 mb-1.5">최초 방문일 (선택)</label>
                        <input
                            type="date"
                            value={form.first_visit_date}
                            onChange={e => setForm(f => ({ ...f, first_visit_date: e.target.value }))}
                            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                        />
                    </div>
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex-1 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            등록
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────
export default function LeadsPage() {
    const { selectedClient } = useClient();
    const [summary, setSummary] = useState<LeadSummary | null>(null);
    const [leads, setLeads] = useState<Lead[]>([]);
    const [loading, setLoading] = useState(false);
    const [showAddModal, setShowAddModal] = useState(false);
    const [channelFilter, setChannelFilter] = useState<string>('');
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const clientId = selectedClient?.id;

    const load = useCallback(async () => {
        if (!clientId) return;
        setLoading(true);
        try {
            const [s, l] = await Promise.all([
                getLeadSummary(clientId),
                getLeads(clientId, { channel: channelFilter || undefined, limit: 100 }),
            ]);
            setSummary(s);
            setLeads(l);
        } catch {
            toast.error('데이터를 불러오지 못했습니다.');
        } finally {
            setLoading(false);
        }
    }, [clientId, channelFilter]);

    useEffect(() => { load(); }, [load]);

    const handleDelete = async (id: string) => {
        if (!confirm('이 리드를 삭제하시겠습니까?')) return;
        setDeletingId(id);
        try {
            await deleteLead(id);
            toast.success('삭제되었습니다.');
            load();
        } catch {
            toast.error('삭제에 실패했습니다.');
        } finally {
            setDeletingId(null);
        }
    };

    if (!clientId) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <Users className="w-12 h-12 mb-3 opacity-30" />
                <p className="font-medium">광고주를 먼저 선택해주세요.</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* 헤더 */}
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">리드 관리</h1>
                    <p className="text-gray-500 mt-1">잠재 고객 유입 현황을 추적하고 전환율을 분석합니다.</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-2xl font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
                >
                    <UserPlus className="w-4 h-4" /> 리드 등록
                </button>
            </div>

            {/* KPI 요약 */}
            {loading && !summary ? (
                <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                </div>
            ) : summary && (
                <>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <KpiCard
                            icon={<Users className="w-5 h-5" />}
                            label="총 리드 수"
                            value={summary.total_leads.toLocaleString()}
                            sub={`이번 달 신규 ${summary.new_this_month}명`}
                            color="#6366f1"
                        />
                        <KpiCard
                            icon={<TrendingUp className="w-5 h-5" />}
                            label="전환율"
                            value={`${summary.conversion_rate}%`}
                            sub={`전환 ${summary.total_conversions}건`}
                            color="#10b981"
                        />
                        <KpiCard
                            icon={<DollarSign className="w-5 h-5" />}
                            label="총 매출"
                            value={`₩${summary.total_revenue.toLocaleString()}`}
                            color="#f59e0b"
                        />
                        <KpiCard
                            icon={<UserPlus className="w-5 h-5" />}
                            label="이번 달 신규"
                            value={summary.new_this_month.toLocaleString()}
                            sub="명"
                            color="#3b82f6"
                        />
                    </div>

                    {/* 채널 분포 */}
                    <ChannelBar by_channel={summary.by_channel} total={summary.total_leads} />
                </>
            )}

            {/* 리드 목록 */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* 필터 바 */}
                <div className="px-6 py-4 border-b border-gray-50 flex items-center gap-3">
                    <Filter className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-500">채널 필터</span>
                    <div className="flex gap-2 flex-wrap">
                        <button
                            onClick={() => setChannelFilter('')}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${channelFilter === '' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                        >
                            전체
                        </button>
                        {CHANNELS.map(c => (
                            <button
                                key={c.value}
                                onClick={() => setChannelFilter(channelFilter === c.value ? '' : c.value)}
                                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${channelFilter === c.value ? 'text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                style={channelFilter === c.value ? { background: c.color } : {}}
                            >
                                {c.label}
                            </button>
                        ))}
                    </div>
                    {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-300 ml-auto" />}
                </div>

                {/* 테이블 */}
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-gray-50 bg-gray-50/50">
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">이름</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">연락처</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">채널</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">코호트</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">최초 방문</th>
                                <th className="px-6 py-3" />
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {leads.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-16 text-gray-400">
                                        <Users className="w-10 h-10 mx-auto mb-3 opacity-20" />
                                        <p>등록된 리드가 없습니다.</p>
                                    </td>
                                </tr>
                            ) : leads.map(lead => (
                                <tr key={lead.id} className="hover:bg-gray-50/50 transition-colors group">
                                    <td className="px-6 py-4 font-medium text-gray-800">
                                        {lead.name || <span className="text-gray-300 italic">이름 없음</span>}
                                    </td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {lead.contact || <span className="text-gray-300 italic">—</span>}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span
                                            className="px-2.5 py-1 rounded-lg text-xs font-semibold text-white"
                                            style={{ background: channelColor(lead.channel) }}
                                        >
                                            {channelLabel(lead.channel)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 font-mono text-xs">{lead.cohort_month}</td>
                                    <td className="px-6 py-4 text-gray-500 text-xs">
                                        {new Date(lead.first_visit_date).toLocaleDateString('ko-KR')}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => handleDelete(lead.id)}
                                            disabled={deletingId === lead.id}
                                            className="p-2 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50"
                                        >
                                            {deletingId === lead.id
                                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                                : <Trash2 className="w-4 h-4" />
                                            }
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {leads.length > 0 && (
                    <div className="px-6 py-3 border-t border-gray-50 text-xs text-gray-400">
                        총 {leads.length}개 리드 표시 중
                    </div>
                )}
            </div>

            {showAddModal && (
                <AddLeadModal
                    clientId={clientId}
                    onClose={() => setShowAddModal(false)}
                    onCreated={() => { setShowAddModal(false); load(); }}
                />
            )}
        </div>
    );
}
