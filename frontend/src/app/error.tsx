'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function RootError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('[RootError]', error);
    }, [error]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full mx-auto p-8 bg-white rounded-2xl shadow-lg text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                    </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                    오류가 발생했습니다
                </h2>
                <p className="text-sm text-gray-500 mb-6">
                    예기치 않은 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
                </p>
                {error.digest && (
                    <p className="text-xs text-gray-400 mb-4 font-mono">
                        오류 코드: {error.digest}
                    </p>
                )}
                <div className="flex gap-3">
                    <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => window.location.href = '/'}
                    >
                        홈으로
                    </Button>
                    <Button
                        className="flex-1"
                        onClick={reset}
                    >
                        다시 시도
                    </Button>
                </div>
            </div>
        </div>
    );
}
