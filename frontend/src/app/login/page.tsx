'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/providers/AuthProvider';
import { login as apiLogin } from '@/lib/api';
import { Loader2, Mail, Lock, Eye, EyeOff, TrendingUp, ShieldCheck, Zap } from 'lucide-react';
import Link from 'next/link';

const FEATURES = [
    { icon: TrendingUp, text: "네이버 검색량·순위 실시간 모니터링" },
    { icon: Zap, text: "4대 SNS 언급량 다중 키워드 분석" },
    { icon: ShieldCheck, text: "키워드별 점유율 추적 및 엑셀 추출" },
];

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const response = await apiLogin(email, password);
            login(response.access_token, response.user as any);
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setError(detail);
            } else {
                setError(
                    err.response
                        ? `서버 오류 (${err.response.status}): 로그인에 실패했습니다.`
                        : '네트워크 연결 오류: 서버에 접속할 수 없습니다.'
                );
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left panel — branding */}
            <div className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 bg-sidebar relative overflow-hidden">
                {/* Background decoration */}
                <div className="absolute inset-0 bg-sidebar" />
                <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-primary/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

                {/* Grid pattern overlay */}
                <div
                    className="absolute inset-0 opacity-[0.03]"
                    style={{
                        backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)',
                        backgroundSize: '32px 32px',
                    }}
                />

                {/* Logo */}
                <div className="relative z-10 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg">
                        <ShieldCheck className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <span className="text-white font-bold text-xl tracking-tight">KeywordLens</span>
                        <span className="ml-2 text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-semibold">
                            Pro
                        </span>
                    </div>
                </div>

                {/* Main copy */}
                <div className="relative z-10 space-y-6">
                    <div>
                        <h1 className="text-4xl font-bold text-white leading-tight tracking-tight">
                            데이터로 읽는<br />
                            <span className="text-primary">
                                마케팅 인사이트
                            </span>
                        </h1>
                        <p className="mt-4 text-white/70 text-base leading-relaxed max-w-sm">
                            네이버 검색량과 4대 SNS 언급량을 다중 키워드로
                            조회·시각화·엑셀 추출까지 한곳에서.
                        </p>
                    </div>

                    {/* Feature list */}
                    <ul className="space-y-3">
                        {FEATURES.map(({ icon: Icon, text }) => (
                            <li key={text} className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                                    <Icon className="w-4 h-4 text-primary" />
                                </div>
                                <span className="text-white/70 text-sm">{text}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Footer */}
                <div className="relative z-10">
                    <p className="text-white/45 text-xs">
                        © 2025 KeywordLens. All rights reserved.
                    </p>
                </div>
            </div>

            {/* Right panel — form */}
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-background">
                {/* Mobile logo */}
                <div className="lg:hidden flex items-center gap-2 mb-8">
                    <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center">
                        <ShieldCheck className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-foreground font-bold text-xl">KeywordLens</span>
                </div>

                <div className="w-full max-w-sm animate-fade-in-up">
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-foreground tracking-tight">다시 오신 것을 환영합니다</h2>
                        <p className="text-muted-foreground text-sm mt-1">계정에 로그인하여 대시보드에 접근하세요.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email or ID */}
                        <div className="space-y-1.5">
                            <label className="text-sm font-semibold text-foreground">이메일 또는 아이디</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                                <input
                                    type="text"
                                    required
                                    autoComplete="username"
                                    placeholder="admin"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-border rounded-xl
                                               text-foreground placeholder-muted-foreground
                                               focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary
                                               transition-all"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1.5">
                            <label className="text-sm font-semibold text-foreground">비밀번호</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    autoComplete="current-password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-10 py-2.5 text-sm bg-card border border-border rounded-xl
                                               text-foreground placeholder-muted-foreground
                                               focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary
                                               transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Error */}
                        {error && (
                            <div className="bg-red-50 border border-red-100 text-red-600 p-3 rounded-xl text-xs font-medium">
                                {error}
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex items-center justify-center py-2.5 px-4 mt-2
                                       text-sm font-semibold text-white
                                       bg-primary hover:bg-primary/90
                                       rounded-xl shadow-lg
                                       focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary
                                       transition-all active:scale-[0.98]
                                       disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                '로그인'
                            )}
                        </button>
                    </form>

                    <p className="text-center text-sm text-muted-foreground mt-6">
                        계정이 없으신가요?{' '}
                        <Link href="/signup" className="font-semibold text-primary hover:text-primary/90 hover:underline">
                            회원가입
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
