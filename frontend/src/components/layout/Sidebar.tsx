'use client';

import {
    LayoutDashboard,
    Database,
    FileText,
    Lightbulb,
    BarChart3,
    Users,
    Settings,
    UserCog,
    Activity
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/providers/AuthProvider';
import clsx from 'clsx';

const serviceItems = [
    { name: '종합 대시보드', href: '/dashboard', icon: LayoutDashboard },
    { name: '성과 효율 리뷰', href: '/efficiency', icon: BarChart3 },
    { name: '리포트 센터', href: '/reports', icon: FileText },
    { name: '심층 분석', href: '/analysis', icon: Database },
    { name: '협업 보드', href: '/collaboration', icon: Users },
];

const adminItems = [
    { name: '사용자 및 권한', href: '/admin/users', icon: UserCog },
    { name: '업체 데이터 관리', href: '/settings', icon: Settings },
    { name: '인프라 현황', href: '/admin/status', icon: Activity },
];

interface SidebarProps {
    isOpen?: boolean;
    onClose?: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
    const pathname = usePathname();
    const { user } = useAuth();


    return (
        <>
            {/* Mobile Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-gray-900/60 backdrop-blur-sm lg:hidden transition-opacity"
                    onClick={onClose}
                    aria-hidden="true"
                />
            )}

            <div className={clsx(
                "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-gray-900 text-white shadow-xl transition-transform duration-300 ease-in-out lg:static lg:translate-x-0",
                isOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="flex h-20 items-center justify-center border-b border-gray-800/50 bg-gray-900/50 backdrop-blur-sm">
                    <div className="flex items-center gap-2">
                        <div className="bg-indigo-600 p-1.5 rounded-lg" aria-hidden="true">
                            <LayoutDashboard className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">D-MIND</span>
                    </div>
                </div>
                <nav className="flex-1 space-y-6 px-3 py-6 overflow-y-auto">
                    <div>
                        <p className="px-4 mb-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Service</p>
                        <div className="space-y-1">
                            {serviceItems.map((item) => {
                                const Icon = item.icon;
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        className={clsx(
                                            'group flex items-center rounded-xl px-4 py-3 text-sm font-bold transition-all duration-200',
                                            isActive
                                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                        )}
                                        aria-current={isActive ? 'page' : undefined}
                                    >
                                        <Icon className={clsx(
                                            "mr-3 h-5 w-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-110",
                                            isActive ? "text-white" : "text-gray-500 group-hover:text-indigo-400"
                                        )} aria-hidden="true" />
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>

                    {(user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN') && (
                        <div>
                            <p className="px-4 mb-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Management</p>
                            <div className="space-y-1">
                                {adminItems.map((item) => {
                                    const Icon = item.icon;
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            className={clsx(
                                                'group flex items-center rounded-xl px-4 py-3 text-sm font-bold transition-all duration-200',
                                                isActive
                                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                                                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                            )}
                                            aria-current={isActive ? 'page' : undefined}
                                        >
                                            <Icon className={clsx(
                                                "mr-3 h-5 w-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-110",
                                                isActive ? "text-white" : "text-gray-500 group-hover:text-indigo-400"
                                            )} aria-hidden="true" />
                                            {item.name}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </nav>

                {user && (
                    <div className="p-4 border-t border-gray-800/50 bg-gray-900/50">
                        <div className="flex items-center gap-3 px-2">
                            <div className="h-8 w-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xs uppercase">
                                {user.name?.[0] || 'U'}
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-xs font-bold text-gray-200 truncate">{user.name}</span>
                                <span className="text-[10px] text-gray-500 font-medium truncate uppercase">{user.role === 'ADMIN' ? 'MASTER' : user.role}</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
