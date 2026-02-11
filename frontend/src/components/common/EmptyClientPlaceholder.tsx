'use client';

import React from 'react';
import Link from 'next/link';
import { Plus, Building2 } from 'lucide-react';

interface EmptyClientPlaceholderProps {
    title?: string;
    description?: string;
}

export function EmptyClientPlaceholder({
    title = "환영합니다!",
    description = "대시보드를 시작하려면 먼저 관리할 업체를 등록해야 합니다."
}: EmptyClientPlaceholderProps) {
    return (
        <div className="flex h-[70vh] flex-col items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="max-w-md w-full text-center space-y-6 bg-white p-10 rounded-2xl border border-gray-100 shadow-sm">
                <div className="bg-indigo-50 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto rotate-3">
                    <Building2 className="w-10 h-10 text-primary -rotate-3" />
                </div>
                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
                    <p className="text-gray-500 text-sm">{description}</p>
                </div>
                <Link
                    href="/settings"
                    className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 text-base font-bold text-white bg-primary rounded-xl hover:bg-opacity-90 transition-all shadow-md active:scale-[0.98]"
                >
                    <Plus className="w-5 h-5" /> 업체 등록하러 가기
                </Link>
                <p className="text-[10px] text-gray-400">
                    * 업체 등록 후 매체(네이버, 구글 등)를 연동하면 실시간 성과 분석 및 AI 리포트 생성이 가능합니다.
                </p>
            </div>
        </div>
    );
}
