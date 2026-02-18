'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Settings, RefreshCw, Home } from 'lucide-react';

export default function SettingsError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('[SettingsError]', error);
    }, [error]);

    return (
        <div className="flex-1 flex items-center justify-center p-6">
            <div className="max-w-lg w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
                <div className="w-14 h-14 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-5">
                    <Settings className="w-7 h-7 text-gray-400" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    설정 페이지 오류
                </h2>
                <p className="text-sm text-gray-500 mb-6">
                    설정을 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
                </p>
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
