"use client";

import { Search } from "lucide-react";
import { NotificationBell } from "@/components/layout/NotificationBell";

export function AppHeader() {
    return (
        <header className="h-16 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-30 px-6 flex items-center justify-between">
            <div className="flex items-center w-full max-w-md">
                <div className="relative w-full">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="검색 (캠페인, 키워드...)"
                        className="w-full h-9 pl-9 pr-4 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    />
                </div>
            </div>

            <div className="flex items-center gap-4">
                {/* Date Range Picker Placeholder */}
                <div className="hidden md:flex items-center px-3 py-1.5 border rounded-md text-sm bg-background hover:bg-accent cursor-pointer">
                    <span className="text-muted-foreground mr-2">기간:</span>
                    <span className="font-medium">최근 30일</span>
                </div>

                <NotificationBell />
            </div>
        </header>
    );
}
