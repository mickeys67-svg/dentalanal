'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { getUsers, createUser, deleteUser } from '@/lib/api';
import { User, UserRole, UserCreate } from '@/types';
import { Plus, Trash2, UserCog, Mail, Shield, UserPlus, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/components/providers/AuthProvider';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

export default function UsersPage() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<FeedbackState>(null);

    const [newEmail, setNewEmail] = useState('');
    const [newName, setNewName] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRole, setNewRole] = useState<UserRole>('VIEWER' as UserRole);

    const showFeedback = (type: 'success' | 'error', message: string) => {
        setFeedback({ type, message });
        setTimeout(() => setFeedback(null), 4000);
    };

    const fetchUsers = useCallback(async () => {
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleAddUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const agencyId = currentUser?.agency_id || '00000000-0000-0000-0000-000000000000';
            await createUser({
                email: newEmail,
                name: newName,
                password: newPassword,
                role: newRole,
                agency_id: agencyId
            });
            setNewEmail('');
            setNewName('');
            setNewPassword('');
            await fetchUsers();
            showFeedback('success', `'${newName}' 계정이 성공적으로 등록되었습니다.`);
        } catch (error: any) {
            console.error(error);
            const msg = error?.response?.data?.detail || '사용자 등록에 실패했습니다.';
            showFeedback('error', msg);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeleteUser = async (id: string, name: string) => {
        // 본인 계정 삭제 방지
        if (id === currentUser?.id) {
            showFeedback('error', '본인 계정은 삭제할 수 없습니다.');
            return;
        }
        if (!window.confirm(`'${name}' 계정을 삭제하시겠습니까?`)) return;
        setDeletingId(id);
        try {
            await deleteUser(id);
            await fetchUsers();
            showFeedback('success', `'${name}' 계정이 삭제되었습니다.`);
        } catch (error) {
            showFeedback('error', '사용자 삭제에 실패했습니다.');
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            {/* 헤더 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-100 p-2 rounded-xl">
                        <UserCog className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">사용자 관리</h1>
                        <p className="text-gray-500 text-sm">플랫폼 계정 및 접근 권한을 관리합니다.</p>
                    </div>
                </div>
                {/* 인라인 피드백 */}
                {feedback && (
                    <div className={clsx(
                        "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                        feedback.type === 'success'
                            ? "bg-green-50 text-green-700 border border-green-200"
                            : "bg-red-50 text-red-700 border border-red-200"
                    )}>
                        {feedback.type === 'success'
                            ? <CheckCircle className="w-4 h-4 shrink-0" />
                            : <XCircle className="w-4 h-4 shrink-0" />
                        }
                        {feedback.message}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                {/* 사용자 등록 폼 */}
                <div className="lg:col-span-1">
                    <ErrorBoundary name="새 사용자 등록 폼">
                    <DashboardWidget title="새 계정 등록">
                        <form onSubmit={handleAddUser} className="p-6 space-y-4">
                            <div className="space-y-1">
                                <label htmlFor="user-email" className="text-xs font-bold text-gray-500 ml-1">이메일</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        id="user-email"
                                        name="email"
                                        type="email"
                                        required
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                        placeholder="user@example.com"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
                                        disabled={isSubmitting}
                                    />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label htmlFor="user-name" className="text-xs font-bold text-gray-500 ml-1">이름</label>
                                <div className="relative">
                                    <UserPlus className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        id="user-name"
                                        name="name"
                                        type="text"
                                        required
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                        placeholder="홍길동"
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                        disabled={isSubmitting}
                                    />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label htmlFor="user-password" className="text-xs font-bold text-gray-500 ml-1">비밀번호</label>
                                <div className="relative">
                                    <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        id="user-password"
                                        name="password"
                                        type="password"
                                        required
                                        minLength={8}
                                        autoComplete="new-password"
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                        placeholder="••••••••"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        disabled={isSubmitting}
                                    />
                                </div>
                                <p className="text-[10px] text-gray-400 ml-1">* 최소 8자 이상</p>
                            </div>
                            <div className="space-y-1">
                                <label htmlFor="user-role" className="text-xs font-bold text-gray-500 ml-1">권한 등급</label>
                                <select
                                    id="user-role"
                                    name="role"
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none appearance-none cursor-pointer"
                                    value={newRole}
                                    onChange={(e) => setNewRole(e.target.value as UserRole)}
                                    disabled={isSubmitting}
                                >
                                    <option value="ADMIN">ADMIN (전체 권한)</option>
                                    <option value="EDITOR">EDITOR (편집 권한)</option>
                                    <option value="VIEWER">VIEWER (조회 권한)</option>
                                </select>
                            </div>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 rounded-xl font-bold text-sm hover:bg-indigo-700 transition-all shadow-md active:scale-[0.98] mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? (
                                    <><Loader2 className="w-4 h-4 animate-spin" /> 등록 중...</>
                                ) : (
                                    <><Plus className="w-4 h-4" /> 계정 생성하기</>
                                )}
                            </button>
                        </form>
                    </DashboardWidget>
                    </ErrorBoundary>
                </div>

                {/* 사용자 목록 */}
                <div className="lg:col-span-2">
                    <ErrorBoundary name="사용자 목록">
                    <DashboardWidget title={`계정 목록 (${users.length}명)`}>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50/50 border-b border-gray-100">
                                    <tr>
                                        <th className="px-6 py-4 text-left font-bold text-gray-500 text-xs uppercase tracking-wider">사용자</th>
                                        <th className="px-6 py-4 text-left font-bold text-gray-500 text-xs uppercase tracking-wider">권한</th>
                                        <th className="px-6 py-4 text-right font-bold text-gray-500 text-xs uppercase tracking-wider">관리</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {isLoading ? (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-12 text-center">
                                                <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto" />
                                            </td>
                                        </tr>
                                    ) : users.length === 0 ? (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-12 text-center text-gray-400 italic text-sm">
                                                등록된 계정이 없습니다.
                                            </td>
                                        </tr>
                                    ) : (
                                        users.map(u => (
                                            <tr key={u.id} className={clsx(
                                                "hover:bg-gray-50/30 transition-colors",
                                                u.id === currentUser?.id && "bg-indigo-50/30"
                                            )}>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center shrink-0">
                                                            <span className="text-xs font-bold text-indigo-600">
                                                                {u.name?.[0]?.toUpperCase() ?? '?'}
                                                            </span>
                                                        </div>
                                                        <div>
                                                            <div className="flex items-center gap-1.5">
                                                                <span className="font-bold text-gray-900">{u.name}</span>
                                                                {u.id === currentUser?.id && (
                                                                    <span className="text-[9px] font-bold bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-full uppercase">나</span>
                                                                )}
                                                            </div>
                                                            <span className="text-xs text-gray-400">{u.email}</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={clsx(
                                                        "px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider",
                                                        u.role === 'ADMIN'
                                                            ? "bg-red-50 text-red-600"
                                                            : u.role === 'EDITOR'
                                                                ? "bg-amber-50 text-amber-600"
                                                                : "bg-gray-100 text-gray-500"
                                                    )}>
                                                        {u.role}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button
                                                        onClick={() => handleDeleteUser(u.id, u.name)}
                                                        disabled={deletingId === u.id || u.id === currentUser?.id}
                                                        className={clsx(
                                                            "p-2 rounded-lg transition-colors",
                                                            u.id === currentUser?.id
                                                                ? "text-gray-200 cursor-not-allowed"
                                                                : "text-gray-300 hover:text-red-500 hover:bg-red-50"
                                                        )}
                                                        aria-label={`${u.name} 계정 삭제`}
                                                        title={u.id === currentUser?.id ? '본인 계정은 삭제할 수 없습니다' : '계정 삭제'}
                                                    >
                                                        {deletingId === u.id ? (
                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                        ) : (
                                                            <Trash2 className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </DashboardWidget>
                    </ErrorBoundary>
                </div>
            </div>
        </div>
    );
}
