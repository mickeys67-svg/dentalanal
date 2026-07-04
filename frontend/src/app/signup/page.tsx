'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createUser, login as apiLogin } from '@/lib/api';
import { useAuth } from '@/components/providers/AuthProvider';
import { UserRole } from '@/types';
import { Loader2, Mail, Lock, User as UserIcon, ShieldCheck, Cake, Eye, EyeOff, CheckCircle2, TrendingUp, Zap } from 'lucide-react';
import Link from 'next/link';

const FEATURES = [
    { icon: TrendingUp, text: "네이버 검색량·순위 실시간 모니터링" },
    { icon: Zap, text: "4대 SNS 언급량 다중 키워드 분석" },
    { icon: ShieldCheck, text: "키워드별 점유율 추적 및 엑셀 추출" },
];

export default function SignupPage() {
    const router = useRouter();
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [name, setName] = useState('');
    const [birthDate, setBirthDate] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            await createUser({ email, name, password, birth_date: birthDate, role: UserRole.ADMIN });
            try {
                const response = await apiLogin(email, password);
                login(response.access_token, response.user as any);
                setSuccess(true);
            } catch {
                setSuccess(true);
                setTimeout(() => router.push('/login'), 2000);
            }
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            if (Array.isArray(detail)) {
                setError(`입력 값이 올바르지 않습니다: ${detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')}`);
            } else if (typeof detail === 'string') {
                setError(detail.includes('이미') || detail.includes('등록') ? `${detail} 로그인 페이지에서 로그인해주세요.` : detail);
            } else {
                setError(err.response ? `서버 오류 (${err.response.status}): 회원가입에 실패했습니다.` : '네트워크 연결 오류: 서버에 접속할 수 없습니다.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const fields = [
        { label: '이름', icon: UserIcon, type: 'text', placeholder: '홍길동', value: name, onChange: setName },
        { label: '생년월일', icon: Cake, type: 'text', placeholder: 'YYYY-MM-DD', value: birthDate, onChange: setBirthDate },
        { label: '이메일', icon: Mail, type: 'email', placeholder: 'admin@example.com', value: email, onChange: setEmail },
    ];

    return (
        <div className="min-h-screen flex">
            {/* Left branding panel */}
            <div className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 bg-sidebar relative overflow-hidden">
                <div className="absolute inset-0 bg-sidebar" />
                <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-primary/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
                <div
                    className="absolute inset-0 opacity-[0.03]"
                    style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '32px 32px' }}
                />

                <div className="relative z-10 flex items-center gap-3">
                    <span className="text-white font-bold text-xl tracking-tight">KeywordLens</span>
                </div>

                <div className="relative z-10 space-y-6">
                    <div>
                        <h1 className="text-4xl font-bold text-white leading-tight tracking-tight">
                            데이터로 읽는<br />
                            <span className="text-primary">
                                마케팅 인사이트
                            </span>
                        </h1>
                        <p className="mt-4 text-white/70 text-base leading-relaxed max-w-sm">
                            KeywordLens로 검색량과 SNS 언급량을 한눈에 파악하고, 다중 키워드 분석으로 인사이트를 얻으세요.
                        </p>
                    </div>
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

                <p className="relative z-10 text-white/45 text-xs">© 2026 KeywordLens. All rights reserved.</p>
            </div>

            {/* Right form panel */}
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-background">
                <div className="lg:hidden flex items-center gap-2 mb-8">
                    <span className="text-foreground font-bold text-xl">KeywordLens</span>
                </div>

                <div className="w-full max-w-sm animate-fade-in-up">
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-foreground tracking-tight">계정 만들기</h2>
                        <p className="text-muted-foreground text-sm mt-1">관리자 계정을 생성하여 마케팅 분석을 시작하세요.</p>
                    </div>

                    {success ? (
                        <div className="flex flex-col items-center gap-4 py-10 animate-fade-in">
                            <div className="w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center">
                                <CheckCircle2 className="w-7 h-7 text-emerald-500" />
                            </div>
                            <div className="text-center">
                                <p className="font-bold text-foreground">회원가입 완료!</p>
                                <p className="text-sm text-muted-foreground mt-1">잠시 후 대시보드로 이동합니다...</p>
                            </div>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {fields.map(({ label, icon: Icon, type, placeholder, value, onChange }) => (
                                <div key={label} className="space-y-1.5">
                                    <label className="text-sm font-semibold text-foreground">{label}</label>
                                    <div className="relative">
                                        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                                        <input
                                            type={type}
                                            required
                                            placeholder={placeholder}
                                            value={value}
                                            onChange={(e) => onChange(e.target.value)}
                                            className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-border rounded-xl
                                                       text-foreground placeholder-muted-foreground
                                                       focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary
                                                       transition-all"
                                        />
                                    </div>
                                </div>
                            ))}

                            {/* Password field (special — toggle) */}
                            <div className="space-y-1.5">
                                <label className="text-sm font-semibold text-foreground">비밀번호</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        required
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

                            {error && (
                                <div className="bg-red-50 border border-red-100 text-red-600 p-3 rounded-xl text-xs font-medium">
                                    {error}
                                </div>
                            )}

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
                                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : '계정 생성하기'}
                            </button>
                        </form>
                    )}

                    <p className="text-center text-sm text-muted-foreground mt-6">
                        이미 계정이 있으신가요?{' '}
                        <Link href="/login" className="font-semibold text-primary hover:text-primary/90 hover:underline">
                            로그인
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
