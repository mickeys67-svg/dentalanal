'use client';

import {
    LayoutDashboard,
    Database,
    FileText,
    Lightbulb,
    BarChart3,
    Users,
    Settings
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const navItems = [
    { name: '종합 대시보드', href: '/dashboard', icon: LayoutDashboard },
    { name: '데이터 수집', href: '/collection', icon: Database },
    { name: '리포트 센터', href: '/reports', icon: FileText },
    { name: 'AI 전략 수립', href: '/strategy', icon: Lightbulb },
    { name: '심층 분석', href: '/analysis', icon: BarChart3 },
    { name: '영업/협업', href: '/collaboration', icon: Users },
    { name: '설정', href: '/settings', icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-full w-64 flex-col bg-gray-900 text-white">
            <div className="flex h-16 items-center justify-center border-b border-gray-800">
                <h1 className="text-xl font-bold">D-MIND</h1>
            </div>
            <nav className="flex-1 space-y-1 px-2 py-4">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={clsx(
                                'group flex items-center rounded-md px-2 py-2 text-sm font-medium',
                                pathname === item.href
                                    ? 'bg-gray-800 text-white'
                                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                            )}
                        >
                            <Icon className="mr-3 h-6 w-6 flex-shrink-0" />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
