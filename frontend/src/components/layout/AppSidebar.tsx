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
    HandCoins,
    Lightbulb,
    Layers,
    Database,
    Search,
    Youtube,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

// badge: "연동" → 외부 계정/데이터 소스 연동 시 실측값이 표출되는 항목(빈 화면 오해 방지).
const menuGroups = [
    {
        label: "개요",
        items: [
            { title: "대시보드", href: "/dashboard", icon: LayoutDashboard },
        ],
    },
    {
        // 핵심 제품 — 실데이터로 작동 (배지 없음)
        label: "키워드·SNS 인텔리전스",
        items: [
            { title: "키워드 검색량", href: "/dashboard/keywords", icon: Search },
            { title: "검색 트렌드", href: "/dashboard/trends", icon: TrendingUp },
            { title: "SNS 언급량", href: "/dashboard/sns", icon: Youtube },
        ],
    },
    {
        label: "광고·성과 분석",
        items: [
            { title: "광고 성과", href: "/dashboard/ads", icon: BarChart3, badge: "연동" },
            { title: "플레이스 순위", href: "/dashboard/place", icon: MapPin },
            { title: "바이럴 모니터링", href: "/dashboard/viral", icon: MessageSquare },
            { title: "심층 분석", href: "/analysis", icon: TrendingUp },
        ],
    },
    {
        label: "대행사 운영",
        items: [
            { title: "리드 관리", href: "/leads", icon: Users },
            { title: "리포트", href: "/reports", icon: FileText },
            { title: "AI 어시스턴트", href: "/assistant", icon: Bot, badge: "연동" },
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
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-sidebar text-sidebar-fg rounded-lg shadow-lg"
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
                    "bg-sidebar text-sidebar-fg shadow-sidebar",
                    "transition-transform duration-300 ease-in-out",
                    "md:translate-x-0",
                    mobileOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo Area */}
                <div className="h-[72px] flex items-center px-6 border-b border-white/10 flex-shrink-0">
                    <div className="flex flex-col gap-0.5">
                        <span className="font-display text-[19px] font-semibold tracking-[0.02em] text-sidebar-fg">
                            KeywordLens
                        </span>
                        <span className="text-[10px] tracking-[0.22em] text-gold uppercase">
                            Marketing Insight
                        </span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-5">
                    {menuGroups.map((group) => (
                        <div key={group.label}>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35 px-3 mb-1.5">
                                {group.label}
                            </p>
                            <div className="space-y-0.5">
                                {group.items.map((item) => {
                                    const active = isActive(item.href);
                                    const badge = (item as { badge?: string }).badge;
                                    return (
                                        <Link
                                            key={item.href}
                                            href={item.href}
                                            onClick={() => setMobileOpen(false)}
                                            className={cn(
                                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium",
                                                "transition-all duration-150",
                                                active
                                                    ? "bg-gold/[0.16] text-gold-bright font-semibold"
                                                    : "text-white/60 hover:bg-white/[0.07] hover:text-white/90"
                                            )}
                                        >
                                            <item.icon
                                                className={cn(
                                                    "h-4 w-4 flex-shrink-0",
                                                    active ? "text-gold-bright" : "text-white/45"
                                                )}
                                            />
                                            <span className="flex-1">{item.title}</span>
                                            {badge && !active && (
                                                <span
                                                    className="text-[9px] font-semibold px-1.5 py-0.5 rounded
                                                               bg-white/10 text-white/45 flex-shrink-0"
                                                    title="외부 소스 연동 시 실측값이 표출됩니다"
                                                >
                                                    {badge}
                                                </span>
                                            )}
                                            {active && (
                                                <ChevronRight className="h-3 w-3 text-gold-bright flex-shrink-0" />
                                            )}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </nav>

                {/* User Profile */}
                <div className="p-3 border-t border-white/10 flex-shrink-0">
                    <div className="flex items-center gap-3 px-2 py-2.5 rounded-lg hover:bg-white/[0.06] transition-colors">
                        <div className="h-9 w-9 rounded-full bg-gold flex items-center justify-center font-display text-sm font-semibold text-sidebar flex-shrink-0">
                            {user?.name?.charAt(0).toUpperCase() || "A"}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-sidebar-fg truncate">
                                {user?.name || "Admin"}
                            </p>
                            <p className="text-xs text-white/45 truncate">
                                {user?.email || "admin@keywordlens.com"}
                            </p>
                        </div>
                        <button
                            onClick={logout}
                            className="p-1.5 text-white/45 hover:text-danger hover:bg-danger/10 rounded-lg transition-colors flex-shrink-0"
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
