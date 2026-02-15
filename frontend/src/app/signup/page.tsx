'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createUser } from '@/lib/api';
import { UserRole } from '@/types';
import { Loader2, Mail, Lock, User as UserIcon, ShieldCheck, Cake, Eye, EyeOff } from 'lucide-react';
import Link from 'next/link';

export default function SignupPage() {
    const router = useRouter();
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
            await createUser({
                email,
                name,
                password,
                birth_date: birthDate,
                role: UserRole.ADMIN
            });
            setSuccess(true);
            setTimeout(() => {
                router.push('/login');
            }, 2000);
        } catch (err: any) {
            console.error('Signup error:', err);
            const detail = err.response?.data?.detail;

            if (Array.isArray(detail)) {
                const messages = detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ');
                setError(`입력 값이 올바르지 않습니다: ${messages}`);
            } else if (typeof detail === 'string') {
                setError(detail);
            } else {
                // Network or Infrastructure error
                const errorMsg = err.response
                    ? `서버 오류 (${err.response.status}): 회원가입에 실패했습니다.`
                    : `네트워크 연결 오류: 서버에 접속할 수 없습니다.`;
                setError(errorMsg);
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
            <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl shadow-indigo-100/50 border border-gray-100">
                <div className="text-center space-y-2">
                    <div className="bg-indigo-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto rotate-3 shadow-lg shadow-indigo-200">
                        <ShieldCheck className="w-10 h-10 text-white" />
                    </div>
                    <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">D-MIND 시작하기</h2>
                    <p className="text-gray-500 font-medium">관리자 계정을 생성하여 마케팅 분석을 시작하세요.</p>
                </div>

                {success ? (
                    <div className="bg-emerald-50 text-emerald-600 p-6 rounded-2xl text-center animate-in fade-in zoom-in">
                        <p className="font-bold text-lg">회원가입 완료!</p>
                        <p className="text-sm">잠시 후 로그인 페이지로 이동합니다...</p>
                    </div>
                ) : (
                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <div className="space-y-1">
                                <label className="text-sm font-bold text-gray-700 ml-1">이름</label>
                                <div className="relative">
                                    <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type="text"
                                        required
                                        className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 text-gray-900 rounded-xl focus:ring-2 focus:ring-indigo-500 transition-all text-sm font-medium"
                                        placeholder="홍길동"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-sm font-bold text-gray-700 ml-1">생년월일</label>
                                <div className="relative">
                                    <Cake className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type="text"
                                        required
                                        className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 text-gray-900 rounded-xl focus:ring-2 focus:ring-indigo-500 transition-all text-sm font-medium"
                                        placeholder="YYYY-MM-DD (예: 1990-01-01)"
                                        value={birthDate}
                                        onChange={(e) => setBirthDate(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-sm font-bold text-gray-700 ml-1">이메일 주소</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type="email"
                                        required
                                        className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 text-gray-900 rounded-xl focus:ring-2 focus:ring-indigo-500 transition-all text-sm font-medium"
                                        placeholder="admin@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-sm font-bold text-gray-700 ml-1">비밀번호</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        required
                                        className="block w-full pl-11 pr-12 py-3 bg-gray-50 border border-gray-200 text-gray-900 rounded-xl focus:ring-2 focus:ring-indigo-500 transition-all text-sm font-medium"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none transition-colors"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="bg-red-50 text-red-600 p-4 rounded-xl text-xs font-bold animate-in shake">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex justify-center py-4 px-4 border border-transparent text-sm font-bold rounded-2xl text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-lg active:scale-[0.98] disabled:opacity-50"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "계정 생성하기"}
                        </button>

                        <div className="text-center mt-4">
                            <span className="text-sm text-gray-500">이미 계정이 있으신가요? </span>
                            <Link href="/login" className="text-sm font-bold text-indigo-600 hover:underline">
                                로그인하기
                            </Link>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
