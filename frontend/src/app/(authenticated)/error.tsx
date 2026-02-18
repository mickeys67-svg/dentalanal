'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default function DashboardError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('[DashboardError]', error);
    }, [error]);

    return (
        <div className="flex-1 flex items-center justify-center p-6">
            <div className="max-w-lg w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
                <div className="w-14 h-14 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-5">
                    <AlertTriangle className="w-7 h-7 text-amber-500" />
                </div>

                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    페이지를 불러오지 못했습니다
                </h2>
                <p className="text-sm text-gray-500 mb-2">
                    데이터를 가져오는 중 문제가 발생했습니다.
                    네트워크 연결을 확인하거나 잠시 후 다시 시도해 주세요.
                </p>

                {process.env.NODE_ENV === 'development' && (
                    <details className="text-left mb-4 mt-4">
                        <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 mb-1">
                            오류 상세 (개발 모드)
                        </summary>
                        <pre className="text-xs text-red-600 bg-red-50 rounded-lg p-3 overflow-auto max-h-32 whitespace-pre-wrap">
                            {error.message}
                        </pre>
                    </details>
                )}

                {error.digest && (
                    <p className="text-xs text-gray-400 mb-4 font-mono">
                        오류 코드: {error.digest}
                    </p>
                )}

                <div className="flex gap-3 mt-6">
                    <Button
                        variant="outline"
                        className="flex-1 gap-2"
                        onClick={() => window.location.href = '/dashboard'}
                    >
                        <Home className="w-4 h-4" />
                        대시보드
                    </Button>
                    <Button
                        className="flex-1 gap-2"
                        onClick={reset}
                    >
                        <RefreshCw className="w-4 h-4" />
                        다시 시도
                    </Button>
                </div>
            </div>
        </div>
    );
}
