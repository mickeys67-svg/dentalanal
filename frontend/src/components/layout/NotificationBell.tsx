"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, CheckCheck, Loader2 } from "lucide-react";
import { getNotifications, markAsRead, markAllAsRead, Notification } from "@/lib/api";
import { cn } from "@/lib/utils";

function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "방금 전";
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
}

const TYPE_COLORS: Record<string, string> = {
    RANKING_DROP: "bg-red-100 text-red-700",
    BUDGET_OVERSPEND: "bg-orange-100 text-orange-700",
    SYSTEM: "bg-blue-100 text-blue-700",
    INFO: "bg-gray-100 text-gray-600",
};

const TYPE_LABELS: Record<string, string> = {
    RANKING_DROP: "순위 급락",
    BUDGET_OVERSPEND: "예산 초과",
    SYSTEM: "시스템",
    INFO: "정보",
};

export function NotificationBell() {
    const [open, setOpen] = useState(false);
    const panelRef = useRef<HTMLDivElement>(null);
    const queryClient = useQueryClient();

    const { data: notifications = [], isLoading } = useQuery<Notification[]>({
        queryKey: ["notifications"],
        queryFn: getNotifications,
        refetchInterval: 60000, // 1분마다 폴링
        refetchOnWindowFocus: true,
    });

    const unreadCount = notifications.filter((n) => !n.is_read).length;

    const readMutation = useMutation({
        mutationFn: (id: string) => markAsRead(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });

    const readAllMutation = useMutation({
        mutationFn: markAllAsRead,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });

    // 패널 외부 클릭 시 닫기
    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [open]);

    const handleItemClick = (n: Notification) => {
        if (!n.is_read) {
            readMutation.mutate(n.id);
        }
        if (n.link) {
            window.location.href = n.link;
        }
    };

    return (
        <div className="relative" ref={panelRef}>
            {/* 벨 버튼 */}
            <button
                onClick={() => setOpen((v) => !v)}
                className="relative p-2 rounded-full hover:bg-accent transition-colors"
                aria-label="알림"
            >
                <Bell className="h-5 w-5 text-muted-foreground" />
                {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 min-w-[16px] h-4 px-0.5 rounded-full bg-red-500 border border-background text-[9px] font-bold text-white flex items-center justify-center">
                        {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                )}
            </button>

            {/* 드롭다운 패널 */}
            {open && (
                <div className="absolute right-0 top-11 w-80 bg-white border rounded-xl shadow-xl z-50 overflow-hidden">
                    {/* 헤더 */}
                    <div className="flex items-center justify-between px-4 py-3 border-b">
                        <span className="font-semibold text-sm">
                            알림
                            {unreadCount > 0 && (
                                <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-red-100 text-red-600 text-[10px] font-bold">
                                    {unreadCount}
                                </span>
                            )}
                        </span>
                        {unreadCount > 0 && (
                            <button
                                onClick={() => readAllMutation.mutate()}
                                disabled={readAllMutation.isPending}
                                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                            >
                                {readAllMutation.isPending ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                    <CheckCheck className="w-3 h-3" />
                                )}
                                모두 읽음
                            </button>
                        )}
                    </div>

                    {/* 알림 목록 */}
                    <div className="max-h-96 overflow-y-auto">
                        {isLoading ? (
                            <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                로딩 중...
                            </div>
                        ) : notifications.length === 0 ? (
                            <div className="py-10 text-center text-sm text-muted-foreground">
                                <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
                                새 알림이 없습니다.
                            </div>
                        ) : (
                            notifications.map((n) => (
                                <button
                                    key={n.id}
                                    onClick={() => handleItemClick(n)}
                                    className={cn(
                                        "w-full text-left px-4 py-3 border-b last:border-b-0 hover:bg-gray-50 transition-colors",
                                        !n.is_read && "bg-blue-50/60"
                                    )}
                                >
                                    <div className="flex items-start gap-2">
                                        {/* 읽음 표시 */}
                                        <div
                                            className={cn(
                                                "w-1.5 h-1.5 rounded-full mt-1.5 shrink-0",
                                                n.is_read ? "bg-transparent" : "bg-blue-500"
                                            )}
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-0.5">
                                                {n.type && (
                                                    <span
                                                        className={cn(
                                                            "px-1.5 py-0.5 rounded text-[10px] font-medium",
                                                            TYPE_COLORS[n.type] ?? TYPE_COLORS.INFO
                                                        )}
                                                    >
                                                        {TYPE_LABELS[n.type] ?? n.type}
                                                    </span>
                                                )}
                                                <span className="text-[11px] text-muted-foreground ml-auto shrink-0">
                                                    {timeAgo(n.created_at)}
                                                </span>
                                            </div>
                                            <p className="text-sm font-medium text-gray-900 truncate">
                                                {n.title}
                                            </p>
                                            {n.content && (
                                                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                                                    {n.content}
                                                </p>
                                            )}
                                        </div>
                                        {!n.is_read && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    readMutation.mutate(n.id);
                                                }}
                                                className="shrink-0 p-1 rounded hover:bg-white text-muted-foreground hover:text-blue-600"
                                                title="읽음 처리"
                                            >
                                                <Check className="w-3 h-3" />
                                            </button>
                                        )}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
