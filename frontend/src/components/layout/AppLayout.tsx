'use client';

import { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { useAuth } from '../providers/AuthProvider';
import { Loader2 } from 'lucide-react';

export function AppLayout({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const { token, isLoading } = useAuth();
    const isAuthPage = pathname === '/login' || pathname === '/signup';

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    if (isAuthPage) {
        return <main className="min-h-screen">{children}</main>;
    }

    if (!token) {
        // Redirection is handled in AuthProvider, but we prevent flash of content here
        return null;
    }

    // New Layout Strategy:
    // AppLayout now only acts as an AuthGuard.
    // The visual layout (Sidebar/Header) is handled by app/dashboard/layout.tsx
    // or specific page layouts.
    return (
        <>
            {children}
        </>
    );
}
