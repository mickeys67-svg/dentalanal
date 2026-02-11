'use client';

import { ReactNode, useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { usePathname } from 'next/navigation';

import { useAuth } from '../providers/AuthProvider';
import { Loader2 } from 'lucide-react';

export function AppLayout({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const { token, isLoading } = useAuth();
    const isAuthPage = pathname === '/login' || pathname === '/signup';
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50">
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

    return (
        <div className="flex h-screen bg-gray-100 overflow-hidden">
            <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
            <div className="flex flex-1 flex-col overflow-hidden">
                <Header onMenuClick={() => setIsSidebarOpen(true)} />
                <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
