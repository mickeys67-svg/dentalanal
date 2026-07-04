"use client";

import { useState } from "react";
import { useClient } from "@/components/providers/ClientProvider";
import { useAuth } from "@/components/providers/AuthProvider";
import { LogOut, User, Bell, Check, ExternalLink, Menu } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getNotifications, markAsRead, markAllAsRead } from "@/lib/api";
import clsx from "clsx";
import Link from "next/link";

interface Notification {
    id: string;
    type: string;
    title: string;
    content: string;
    created_at: string;
    is_read: boolean;
    link?: string;
}

interface HeaderProps {
    onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
    const { clients, selectedClient, setSelectedClient, isLoading: isClientsLoading } = useClient();
    const { user, logout } = useAuth();
    const [isNotifOpen, setIsNotifOpen] = useState(false);
    const queryClient = useQueryClient();

    const { data: notifications = [] } = useQuery<Notification[]>({
        queryKey: ['notifications'],
        queryFn: async () => {
            try {
                return await getNotifications();
            } catch (err) {
                // @ts-expect-error - err is unknown
                if (err.response?.status === 404) {
                    console.debug('Notifications endpoint not available yet');
                } else {
                    const message = err instanceof Error ? err.message : String(err);
                    console.warn('Notifications fetch failed:', message);
                }
                return [];
            }
        },
        enabled: !!user, // Only fetch if authenticated
        refetchInterval: 120000, // 2 minutes
        retry: false,
        staleTime: 60000,
    });

    const unreadCount = notifications.filter((n) => !n.is_read).length;

    const readMutation = useMutation({
        mutationFn: (id: string) => markAsRead(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] })
    });

    const readAllMutation = useMutation({
        mutationFn: markAllAsRead,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] })
    });

    return (
        <header className="bg-card border-b border-border h-16 flex items-center shrink-0">
            <div className="w-full max-w-7xl mx-auto px-6 flex justify-between items-center relative">
                <div className="flex items-center gap-3 lg:gap-6 min-w-0">
                    <button
                        onClick={onMenuClick}
                        className="p-2 -ml-2 text-muted-foreground hover:text-primary lg:hidden"
                        aria-label="메뉴 열기"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                    <p className="text-sm border-none bg-background rounded-md px-2 py-1 focus:ring-0 cursor-pointer text-primary truncate">통합 분석 솔루션</p>
                    <div className="hidden sm:block h-6 w-px bg-border"></div>
                    <div className="hidden md:flex items-center gap-2 truncate">
                        <label htmlFor="client-selector" className="text-xs font-bold text-muted-foreground uppercase tracking-wider">브랜드:</label>
                        <select
                            id="client-selector"
                            name="client-id"
                            value={selectedClient?.id || ""}
                            onChange={(e) => {
                                const client = clients.find(c => c.id === e.target.value);
                                if (client) setSelectedClient(client);
                            }}
                            className="text-sm font-semibold border-none bg-background rounded-md px-2 py-1 focus:ring-0 cursor-pointer text-primary"
                            aria-label="분석 대상 브랜드 선택"
                        >
                            {clients.length === 0 && (
                                <option value="">{isClientsLoading ? "로딩 중..." : "브랜드 없음"}</option>
                            )}
                            {clients.map(client => (
                                <option key={client.id} value={client.id}>
                                    {client.name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    {/* Notification Component */}
                    <div className="relative">
                        <button
                            onClick={() => setIsNotifOpen(!isNotifOpen)}
                            className="p-2.5 rounded-xl bg-background text-muted-foreground hover:bg-secondary hover:text-primary transition-all relative"
                            aria-label={`알림 내역 확인 ${unreadCount > 0 ? `(안 읽은 알림 ${unreadCount}개)` : ''}`}
                            aria-expanded={isNotifOpen}
                        >
                            <Bell className="w-5 h-5" />
                            {unreadCount > 0 && (
                                <span className="absolute top-2 right-2 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white">
                                    {unreadCount > 9 ? '9+' : unreadCount}
                                </span>
                            )}
                        </button>

                        {/* Dropdown Backdrop */}
                        {isNotifOpen && (
                            <div
                                className="fixed inset-0 z-20"
                                onClick={() => setIsNotifOpen(false)}
                            />
                        )}

                        {/* Dropdown Menu */}
                        {isNotifOpen && (
                            <div className="absolute right-0 mt-3 w-80 bg-card rounded-2xl shadow-2xl border border-border py-4 z-30 animate-in fade-in zoom-in duration-200">
                                <div className="px-5 pb-3 border-b border-border flex items-center justify-between">
                                    <h3 className="font-bold text-foreground text-sm">최근 알림</h3>
                                    <button
                                        onClick={() => readAllMutation.mutate()}
                                        className="text-[11px] font-bold text-primary hover:underline"
                                    >
                                        모두 읽음
                                    </button>
                                </div>
                                <div className="max-h-96 overflow-y-auto">
                                    {notifications.length === 0 ? (
                                        <div className="py-12 text-center text-muted-foreground">
                                            <Bell className="w-8 h-8 mx-auto mb-2 opacity-10" />
                                            <p className="text-xs">새로운 알림이 없습니다.</p>
                                        </div>
                                    ) : (
                                        notifications.map((n) => (
                                            <div
                                                key={n.id}
                                                className={clsx(
                                                    "px-5 py-4 hover:bg-secondary transition-colors border-b border-border group",
                                                    !n.is_read && "bg-primary/5"
                                                )}
                                            >
                                                <div className="flex justify-between items-start mb-1">
                                                    <span className={clsx(
                                                        "text-[10px] font-bold px-1.5 py-0.5 rounded",
                                                        n.type === 'NOTICE' ? "bg-amber-100 text-amber-600" : "bg-primary/15 text-primary"
                                                    )}>
                                                        {n.type}
                                                    </span>
                                                    <span className="text-[9px] text-muted-foreground">{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                </div>
                                                <h4 className="text-[12px] font-bold text-foreground line-clamp-1">{n.title}</h4>
                                                <p className="text-[11px] text-muted-foreground mt-0.5 line-clamp-2">{n.content}</p>

                                                <div className="flex items-center gap-3 mt-3">
                                                    {n.link && (
                                                        <Link
                                                            href={n.link}
                                                            className="flex items-center gap-1 text-[10px] font-bold text-primary hover:underline"
                                                            onClick={() => {
                                                                if (!n.is_read) readMutation.mutate(n.id);
                                                                setIsNotifOpen(false);
                                                            }}
                                                        >
                                                            <ExternalLink className="w-3 h-3" /> 이동하기
                                                        </Link>
                                                    )}
                                                    {!n.is_read && (
                                                        <button
                                                            onClick={() => readMutation.mutate(n.id)}
                                                            className="ml-auto text-[10px] font-bold text-muted-foreground/60 hover:text-green-500 flex items-center gap-1"
                                                        >
                                                            <Check className="w-3 h-3" /> 읽음 표시
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="flex items-center gap-3 border-r border-border pr-6">
                        <div className="flex flex-col items-end">
                            <span className="text-sm font-bold text-foreground">{user?.name || '사용자'}님</span>
                            <span className="text-[10px] text-primary font-bold tracking-tighter uppercase">{user?.role} 권한</span>
                        </div>
                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary font-bold text-sm ring-2 ring-white shadow-sm">
                            <User className="w-5 h-5" />
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="flex items-center gap-2 text-muted-foreground hover:text-red-500 transition-colors text-xs font-bold"
                        title="로그아웃"
                        aria-label="로그아웃"
                    >
                        <LogOut className="w-4 h-4" aria-hidden="true" />
                        로그아웃
                    </button>
                </div>
            </div>
        </header>
    );
}
