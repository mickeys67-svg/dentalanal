'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ShieldAlert, RefreshCw, Home } from 'lucide-react';

export default function AdminError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('[AdminError]', error);
    }, [error]);

    return (
        <div className="flex-1 flex items-center justify-center p-6">
            <div className="max-w-lg w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
                <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-5">
                    <ShieldAlert className="w-7 h-7 text-red-500" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    관리자 페이지 오류
                </h2>
                <p className="text-sm text-gray-500 mb-6">
                    관리자 기능을 불러오는 중 오류가 발생했습니다.<br />
                    권한을 확인하거나 잠시 후 다시 시도해 주세요.
                </p>
                {process.env.NODE_ENV === 'development' && (
                    <details className="text-left mb-4">
                        <summary className="text-xs text-gray-400 cursor-pointer mb-1">오류 상세</summary>
                        <pre className="text-xs text-red-600 bg-red-50 rounded-lg p-3 overflow-auto max-h-32 whitespace-pre-wrap">
                            {error.message}
                        </pre>
                    </details>
                )}
                <div className="flex gap-3">
                    <Button variant="outline" className="flex-1 gap-2" onClick={() => window.location.href = '/dashboard'}>
                        <Home className="w-4 h-4" /> 대시보드
                    </Button>
                    <Button className="flex-1 gap-2" onClick={reset}>
                        <RefreshCw className="w-4 h-4" /> 다시 시도
                    </Button>
                </div>
            </div>
        </div>
    );
}
