'use client';

import React, { useState, useEffect } from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { getUsers, createUser, deleteUser } from '@/lib/api';
import { User, UserRole, UserCreate } from '@/types';
import { Plus, Trash2, UserCog, Mail, Shield, UserPlus } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/components/providers/AuthProvider';

export default function UsersPage() {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [newEmail, setNewEmail] = useState('');
    const [newName, setNewName] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRole, setNewRole] = useState<UserRole>('VIEWER' as UserRole);

    const fetchUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleAddUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Use current user's agency_id or fall back to default if not available
            const agencyId = user?.agency_id || '00000000-0000-0000-0000-000000000000';

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
            fetchUsers();
            alert('사용자가 성공적으로 등록되었습니다.');
        } catch (error) {
            console.error(error);
            alert('사용자 등록에 실패했습니다.');
        }
    };

    const handleDeleteUser = async (id: string) => {
        if (!confirm('정말 이 사용자를 삭제하시겠습니까?')) return;
        try {
            await deleteUser(id);
            fetchUsers();
        } catch (error) {
            alert('사용자 삭제에 실패했습니다.');
        }
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-100 p-2 rounded-xl">
                        <UserCog className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">관리자 설정</h1>
                        <p className="text-gray-500">플랫폼 관리자 계정 및 권한을 관리합니다.</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                {/* User Creation Form */}
                <div className="lg:col-span-1">
                    <DashboardWidget title="새 관리자 등록">
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
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                        placeholder="user@example.com"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
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
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                        placeholder="관리자 이름"
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
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
                                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                                        placeholder="••••••••"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                    />
                                </div>
                                <p className="text-[10px] text-gray-400 ml-1">* 최소 8자 이상 입력해 주세요.</p>
                            </div>
                            <div className="space-y-1">
                                <label htmlFor="user-role" className="text-xs font-bold text-gray-500 ml-1">권한 등급</label>
                                <select
                                    id="user-role"
                                    name="role"
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all appearance-none cursor-pointer"
                                    value={newRole}
                                    onChange={(e) => setNewRole(e.target.value as UserRole)}
                                >
                                    <option value="ADMIN">MASTER (전체 권한)</option>
                                    <option value="EDITOR">EDITOR (편집 권한)</option>
                                    <option value="VIEWER">VIEWER (조회 권한)</option>
                                </select>
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-primary text-white py-3 rounded-xl font-bold text-sm hover:bg-opacity-90 transition-all shadow-md active:scale-[0.98] mt-2"
                            >
                                계정 생성하기
                            </button>
                        </form>
                    </DashboardWidget>
                </div>

                {/* Users List */}
                <div className="lg:col-span-2">
                    <DashboardWidget title="관리자 계정 목록">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50/50 border-b border-gray-100">
                                    <tr>
                                        <th className="px-6 py-4 text-left font-bold text-gray-500">관리자 정보</th>
                                        <th className="px-6 py-4 text-left font-bold text-gray-500">권한 등급</th>
                                        <th className="px-6 py-4 text-right font-bold text-gray-500">액션</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {users.map(user => (
                                        <tr key={user.id} className="hover:bg-gray-50/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="font-bold text-gray-900">{user.name}</span>
                                                    <span className="text-xs text-gray-400 font-medium">{user.email}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={clsx(
                                                    "px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider",
                                                    user.role === 'ADMIN' ? "bg-red-50 text-red-600" :
                                                        user.role === 'EDITOR' ? "bg-amber-50 text-amber-600" :
                                                            "bg-gray-100 text-gray-600"
                                                )}>
                                                    {user.role === 'ADMIN' ? 'MASTER' : user.role}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    onClick={() => handleDeleteUser(user.id)}
                                                    className="p-2 text-gray-300 hover:text-red-500 transition-colors"
                                                    aria-label={`${user.name} 계정 삭제`}
                                                >
                                                    <Trash2 className="w-4 h-4" aria-hidden="true" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {users.length === 0 && !isLoading && (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-12 text-center text-gray-400 italic">
                                                등록된 관리자 계정이 없습니다.
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
    );
}
