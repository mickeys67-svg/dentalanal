'use client';

import Link from 'next/link';
import { LayoutDashboard, ArrowLeft } from 'lucide-react';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[70vh] px-6 text-center animate-in fade-in duration-700">
            <div className="bg-primary/10 w-24 h-24 rounded-3xl flex items-center justify-center mb-8 rotate-3 shadow-sm">
                <LayoutDashboard className="w-12 h-12 text-primary -rotate-3" />
            </div>

            <h1 className="text-6xl font-black text-foreground mb-4 tracking-tighter">404</h1>
            <h2 className="text-2xl font-bold text-foreground mb-2">페이지를 찾을 수 없습니다</h2>
            <p className="text-muted-foreground mb-10 max-w-md mx-auto">
                요청하신 페이지가 삭제되었거나 주소가 변경되었을 수 있습니다.<br />
                대시보드로 돌아가 마케팅 성과를 계속해서 분석해보세요.
            </p>

            <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-8 py-4 bg-primary text-white font-bold rounded-2xl hover:bg-primary/90 transition-all shadow-lg active:scale-[0.98]"
            >
                <ArrowLeft className="w-5 h-5" /> 대시보드로 돌아가기
            </Link>

            <div className="mt-16 grid grid-cols-2 gap-4 text-left max-w-sm w-full">
                <div className="p-4 rounded-xl border border-border bg-card/50">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">인기 페이지</span>
                    <Link href="/efficiency" className="text-xs font-bold text-foreground hover:text-primary">성과 효율 리뷰</Link>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card/50">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">데이터 분석</span>
                    <Link href="/analysis" className="text-xs font-bold text-foreground hover:text-primary">심층 분석 센터</Link>
                </div>
            </div>
        </div>
    );
}
