"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    BarChart3,
    MapPin,
    MessageSquare,
    Settings,
    PieChart,
    Users,
    LogOut,
    Menu,
    X,
    ChevronRight,
    TrendingUp,
    FileText,
    Bot,
    BrainCircuit,
    HandCoins,
    Lightbulb,
    Layers,
    Database,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

const menuGroups = [
    {
        label: "개요",
        items: [
            { title: "대시보드", href: "/dashboard", icon: LayoutDashboard },
        ],
    },
    {
        label: "성과 분석",
        items: [
            { title: "광고 성과", href: "/dashboard/ads", icon: BarChart3 },
            { title: "플레이스 순위", href: "/dashboard/place", icon: MapPin },
            { title: "바이럴 모니터링", href: "/dashboard/viral", icon: MessageSquare },
            { title: "심층 분석", href: "/analysis", icon: TrendingUp },
        ],
    },
    {
        label: "비즈니스",
        items: [
            { title: "리드 관리", href: "/leads", icon: Users },
            { title: "리포트", href: "/reports", icon: FileText },
            { title: "AI 어시스턴트", href: "/assistant", icon: Bot },
            { title: "전략 플래너", href: "/strategy", icon: Lightbulb },
        ],
    },
    {
        label: "시스템",
        items: [
            { title: "데이터 수집", href: "/collection", icon: Database },
            { title: "설정", href: "/settings", icon: Settings },
        ],
    },
];

export function AppSidebar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    const isActive = (href: string) =>
        pathname === href || pathname?.startsWith(href + "/");

    return (
        <>
            {/* Mobile Toggle Button */}
            <button
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-slate-900 text-white rounded-lg shadow-lg"
                onClick={() => setMobileOpen(!mobileOpen)}
                aria-label="메뉴"
            >
                {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* Mobile Overlay */}
            {mobileOpen && (
                <div
                    className="md:hidden fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-40 w-64 flex flex-col",
                    "bg-slate-900 shadow-sidebar",
                    "transition-transform duration-300 ease-in-out",
                    "md:translate-x-0",
                    mobileOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo Area */}
                <div className="h-16 flex items-center px-5 border-b border-slate-800 flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 flex-shrink-0">
                            <BrainCircuit className="h-[18px] w-[18px] text-white" />
                        </div>
                        <div className="flex items-baseline gap-1.5">
                            <span className="text-white font-bold text-[15px] tracking-tight">D-MIND</span>
                            <span className="text-[9px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-semibold tracking-wide">
                                Pro
                            </span>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-5">
                    {menuGroups.map((group) => (
                        <div key={group.label}>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500 px-3 mb-1.5">
                                {group.label}
                            </p>
                            <div className="space-y-0.5">
                                {group.items.map((item) => {
                                    const active = isActive(item.href);
                                    return (
                                        <Link
                                            key={item.href}
                                            href={item.href}
                                            onClick={() => setMobileOpen(false)}
                                            className={cn(
                                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium",
                                                "transition-all duration-150",
                                                active
                                                    ? "bg-indigo-500/10 text-indigo-400"
                                                    : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-200"
                                            )}
                                        >
                                            <item.icon
                                                className={cn(
                                                    "h-4 w-4 flex-shrink-0",
                                                    active ? "text-indigo-400" : "text-slate-500"
                                                )}
                                            />
                                            <span className="flex-1">{item.title}</span>
                                            {active && (
                                                <ChevronRight className="h-3 w-3 text-indigo-400 flex-shrink-0" />
                                            )}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </nav>

                {/* User Profile */}
                <div className="p-3 border-t border-slate-800 flex-shrink-0">
                    <div className="flex items-center gap-3 px-2 py-2.5 rounded-lg hover:bg-slate-800 transition-colors">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                            {user?.name?.charAt(0).toUpperCase() || "A"}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-200 truncate">
                                {user?.name || "Admin"}
                            </p>
                            <p className="text-xs text-slate-500 truncate">
                                {user?.email || "admin@dmind.com"}
                            </p>
                        </div>
                        <button
                            onClick={logout}
                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors flex-shrink-0"
                            title="로그아웃"
                        >
                            <LogOut className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
