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
    Menu,
    X,
    PieChart,
    Users,
    LogOut
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

const menuItems = [
    {
        title: "대시보드",
        href: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "광고 성과",
        href: "/dashboard/ads",
        icon: BarChart3,
    },
    {
        title: "플레이스 순위",
        href: "/dashboard/place",
        icon: MapPin,
    },
    {
        title: "바이럴 모니터링",
        href: "/dashboard/viral",
        icon: MessageSquare,
    },
    {
        title: "리드 관리",
        href: "/leads",
        icon: Users,
    },
    {
        title: "리포트",
        href: "/reports",
        icon: PieChart,
    },
    {
        title: "설정",
        href: "/settings",
        icon: Settings,
    },
];

export function AppSidebar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(true);

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-background border rounded-md"
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* Sidebar Container */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-40 w-64 bg-card border-r transition-transform duration-300 ease-in-out md:translate-x-0",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="flex flex-col h-full">
                    {/* Logo Area */}
                    <div className="h-16 flex items-center px-6 border-b">
                        <span className="text-xl font-bold text-primary">DentalAnal</span>
                        <span className="ml-1 text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">2.0</span>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-3 py-4 space-y-1">
                        {menuItems.map((item) => {
                            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
                                        isActive
                                            ? "bg-primary/10 text-primary"
                                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                    )}
                                >
                                    <item.icon className={cn("mr-3 h-5 w-5", isActive ? "text-primary" : "text-muted-foreground")} />
                                    {item.title}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Profile / Logout */}
                    <div className="p-4 border-t space-y-3">
                        <div className="flex items-center">
                            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                                {user?.name?.charAt(0).toUpperCase() || 'A'}
                            </div>
                            <div className="ml-3 flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{user?.name || 'Administrator'}</p>
                                <p className="text-xs text-muted-foreground truncate">{user?.email || 'admin@dental.com'}</p>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            className="w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-md transition-colors"
                        >
                            <LogOut className="h-4 w-4 mr-2" />
                            로그아웃
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
