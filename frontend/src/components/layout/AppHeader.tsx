"use client";

import { Search, ChevronDown, CalendarDays } from "lucide-react";
import { NotificationBell } from "@/components/layout/NotificationBell";

export function AppHeader() {
    return (
        <header className="h-16 border-b border-slate-100 bg-white sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between gap-4">
            {/* Left: Search — hidden on mobile (leave room for mobile toggle) */}
            <div className="hidden md:flex items-center flex-1 max-w-xs">
                <div className="relative w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <input
                        type="text"
                        placeholder="캠페인, 키워드 검색..."
                        className="w-full h-9 pl-9 pr-4 text-sm bg-slate-50 border border-slate-200 rounded-lg
                                   text-slate-700 placeholder-slate-400
                                   focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-300
                                   transition-all"
                    />
                </div>
            </div>

            {/* Mobile spacer for hamburger button */}
            <div className="md:hidden w-10" />

            {/* Right area */}
            <div className="flex items-center gap-2">
                {/* Date range pill */}
                <button className="hidden md:flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-200 rounded-lg
                                   text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors">
                    <CalendarDays className="h-3.5 w-3.5 text-slate-400" />
                    <span className="text-slate-400 text-xs">기간:</span>
                    <span className="font-medium text-slate-700">최근 30일</span>
                    <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                </button>

                <NotificationBell />
            </div>
        </header>
    );
}
