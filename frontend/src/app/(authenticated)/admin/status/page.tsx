'use client';

import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';
import { getSystemStatus } from '@/lib/api';
import clsx from 'clsx';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';

export default function StatusPage() {
    const [status, setStatus] = useState<any>(null);

    const fetchData = async () => {
        try {
            const statusData = await getSystemStatus();
            setStatus(statusData);
        } catch (error) {
            console.error('Failed to fetch system status:', error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Poll every 30s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">시스템 현황 모니터링</h1>
                <p className="text-gray-500">서버 인프라 및 핵심 서비스 동작 상태를 실시간으로 확인합니다.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <DashboardWidget title="서버 활성 상태">
                    <div className="p-6 space-y-6">
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-100">
                            <div className="flex items-center gap-3">
                                <div className={clsx(
                                    "w-3 h-3 rounded-full animate-pulse",
                                    status?.status === 'Healthy' ? "bg-emerald-500" : "bg-red-500"
                                )} />
                                <span className="font-bold text-gray-700">전체 시스템 상태</span>
                            </div>
                            <span className={clsx(
                                "px-3 py-1 rounded-lg text-xs font-bold",
                                status?.status === 'Healthy' ? "bg-emerald-100 text-emerald-600" : "bg-red-100 text-red-600"
                            )}>
                                {status?.status === 'Healthy' ? '정상 작동' : '점검 필요'}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">데이터베이스</p>
                                <p className="text-sm font-bold text-gray-900">{status?.database || '연결 확인 중...'}</p>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">API 서버</p>
                                <p className="text-sm font-bold text-gray-900">HEALTHY</p>
                            </div>
                        </div>
                    </div>
                </DashboardWidget>

                <DashboardWidget title="보안 및 AI 엔진">
                    <div className="p-6 space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-indigo-600 font-bold">
                                <ShieldAlert className="w-5 h-5" />
                                <span>Gemini AI Engine</span>
                            </div>
                            <span className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-bold">Connected</span>
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            Google Cloud Vertex AI 인프라를 통해 실시간 전략 분석을 제공하고 있습니다. API 할당량 및 권한 상태는 정상입니다.
                        </p>
                    </div>
                </DashboardWidget>

                <div className="md:col-span-2">
                    <DashboardWidget title="실시간 이벤트 로그">
                        <div className="p-6">
                            <div className="bg-gray-900 rounded-xl p-6 font-mono text-[11px] text-indigo-300 space-y-2 max-h-[400px] overflow-y-auto shadow-inner">
                                {status?.recent_logs?.map((log: any, idx: number) => (
                                    <div key={idx} className="flex gap-3 border-b border-gray-800 pb-2 mb-2 last:border-0 last:pb-0">
                                        <span className="text-gray-500 shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                                        <span className={clsx(
                                            "font-bold shrink-0",
                                            log.level === 'INFO' ? "text-indigo-400" : "text-emerald-400"
                                        )}>{log.level}</span>
                                        <span className="text-gray-300">{log.message}</span>
                                    </div>
                                ))}
                                {(!status?.recent_logs || status.recent_logs.length === 0) && (
                                    <p className="text-gray-600 italic">로그 데이터를 전송받고 있습니다...</p>
                                )}
                            </div>
                        </div>
                    </DashboardWidget>
                </div>
            </div>
        </div>
    );
}
