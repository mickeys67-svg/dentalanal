'use client';

import { useEffect } from 'react';

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('[GlobalError]', error);
    }, [error]);

    return (
        <html lang="ko">
            <body>
                <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="max-w-md w-full mx-auto p-8 bg-white rounded-2xl shadow-lg text-center">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                />
                            </svg>
                        </div>
                        <h1 className="text-xl font-bold text-gray-900 mb-2">
                            심각한 오류가 발생했습니다
                        </h1>
                        <p className="text-sm text-gray-500 mb-6">
                            애플리케이션을 불러오는 중 문제가 발생했습니다.<br />
                            페이지를 새로고침하거나 잠시 후 다시 시도해 주세요.
                        </p>
                        {error.digest && (
                            <p className="text-xs text-gray-400 mb-4 font-mono">
                                오류 코드: {error.digest}
                            </p>
                        )}
                        <button
                            onClick={reset}
                            className="w-full py-2.5 px-4 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
                        >
                            다시 시도
                        </button>
                    </div>
                </div>
            </body>
        </html>
    );
}
