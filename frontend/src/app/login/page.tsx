'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/providers/AuthProvider';
import { login as apiLogin } from '@/lib/api';
import { Loader2, Mail, Lock, Eye, EyeOff, TrendingUp, ShieldCheck, Zap } from 'lucide-react';
import Link from 'next/link';

const FEATURES = [
    { icon: TrendingUp, text: "실시간 광고 성과 및 순위 모니터링" },
    { icon: Zap, text: "Gemini AI 기반 마케팅 전략 제안" },
    { icon: ShieldCheck, text: "경쟁사 분석 및 SOV 점유율 추적" },
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
            <div className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 bg-slate-900 relative overflow-hidden">
                {/* Background decoration */}
                <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900" />
                <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

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
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                        <ShieldCheck className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <span className="text-white font-bold text-xl tracking-tight">D-MIND</span>
                        <span className="ml-2 text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-semibold">
                            Pro
                        </span>
                    </div>
                </div>

                {/* Main copy */}
                <div className="relative z-10 space-y-6">
                    <div>
                        <h1 className="text-4xl font-bold text-white leading-tight tracking-tight">
                            데이터 기반의<br />
                            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                                스마트한 치과 경영
                            </span>
                        </h1>
                        <p className="mt-4 text-slate-400 text-base leading-relaxed max-w-sm">
                            광고 성과, 순위 모니터링, AI 분석을 하나의 플랫폼에서.
                            경쟁사를 앞서는 데이터 전략을 시작하세요.
                        </p>
                    </div>

                    {/* Feature list */}
                    <ul className="space-y-3">
                        {FEATURES.map(({ icon: Icon, text }) => (
                            <li key={text} className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                                    <Icon className="w-4 h-4 text-indigo-400" />
                                </div>
                                <span className="text-slate-300 text-sm">{text}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Footer */}
                <div className="relative z-10">
                    <p className="text-slate-600 text-xs">
                        © 2025 D-MIND Enterprise. All rights reserved.
                    </p>
                </div>
            </div>

            {/* Right panel — form */}
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50">
                {/* Mobile logo */}
                <div className="lg:hidden flex items-center gap-2 mb-8">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                        <ShieldCheck className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-slate-900 font-bold text-xl">D-MIND</span>
                </div>

                <div className="w-full max-w-sm animate-fade-in-up">
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">다시 오신 것을 환영합니다</h2>
                        <p className="text-slate-500 text-sm mt-1">계정에 로그인하여 대시보드에 접근하세요.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email */}
                        <div className="space-y-1.5">
                            <label className="text-sm font-semibold text-slate-700">이메일</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                <input
                                    type="email"
                                    required
                                    placeholder="admin@dmind.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-white border border-slate-200 rounded-xl
                                               text-slate-900 placeholder-slate-400
                                               focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-400
                                               transition-all"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1.5">
                            <label className="text-sm font-semibold text-slate-700">비밀번호</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    autoComplete="current-password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-10 py-2.5 text-sm bg-white border border-slate-200 rounded-xl
                                               text-slate-900 placeholder-slate-400
                                               focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-400
                                               transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
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
                                       bg-indigo-600 hover:bg-indigo-700
                                       rounded-xl shadow-lg shadow-indigo-200
                                       focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
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

                    <p className="text-center text-sm text-slate-500 mt-6">
                        계정이 없으신가요?{' '}
                        <Link href="/signup" className="font-semibold text-indigo-600 hover:text-indigo-700 hover:underline">
                            회원가입
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
