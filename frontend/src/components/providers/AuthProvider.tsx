'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import axios from 'axios';

interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    agency_id: string | null;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, user: User) => void;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser && storedToken !== 'null' && storedToken !== 'undefined') {
            try {
                setToken(storedToken);
                setUser(JSON.parse(storedUser));
                axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
            } catch (e) {
                console.error("Failed to parse stored user", e);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        } else {
            // Clean up potentially corrupt state
            if (storedToken === 'null' || storedToken === 'undefined') {
                localStorage.removeItem('token');
            }
        }
        setIsLoading(false);
    }, [router]);

    const login = useCallback((newToken: string, newUser: User) => {
        setToken(newToken);
        setUser(newUser);
        localStorage.setItem('token', newToken);
        localStorage.setItem('user', JSON.stringify(newUser));
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
        router.push('/dashboard');
    }, [router]);

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
        router.push('/login');
    }, [router]);

    // Protect routes
    useEffect(() => {
        if (!isLoading) {
            const isAuthPage = pathname === '/login' || pathname === '/signup';
            if (!token && !isAuthPage) {
                router.push('/login');
            } else if (token && isAuthPage) {
                router.push('/dashboard');
            }
        }
    }, [token, isLoading, pathname, router]);

    // 401 처리는 lib/api.ts의 axios 인스턴스 인터셉터에서 일괄 처리
    // (axios.defaults에 붙이면 api 인스턴스에 미적용되므로 중복 제거)

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
