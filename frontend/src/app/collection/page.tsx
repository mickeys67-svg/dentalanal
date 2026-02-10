"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getConnectors, getActiveConnections, connectPlatform } from '@/lib/api';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import { Loader2, Link2, ExternalLink, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { Connector } from '@/types';
import { Notification, NotificationType } from '@/components/common/Notification';

export default function CollectionPage() {
    const queryClient = useQueryClient();
    const clientId = "c1"; // Demo clientId
    const [notification, setNotification] = useState<{ message: string; type: NotificationType } | null>(null);

    const { data: connectorsData, isLoading: isConnectorsLoading } = useQuery({
        queryKey: ['connectors'],
        queryFn: getConnectors
    });

    const { data: activeConnections, isLoading: isActiveLoading } = useQuery({
        queryKey: ['activeConnections', clientId],
        queryFn: () => getActiveConnections(clientId)
    });

    const connectMutation = useMutation({
        mutationFn: ({ platformId, creds }: { platformId: string, creds: any }) =>
            connectPlatform(platformId, clientId, creds),
        onSuccess: (data) => {
            setNotification({ message: data.message, type: 'SUCCESS' });
            queryClient.invalidateQueries({ queryKey: ['activeConnections'] });
        },
        onError: (error: any) => {
            setNotification({ message: error.response?.data?.detail || "연동 실패", type: 'ERROR' });
        }
    });

    if (isConnectorsLoading || isActiveLoading) {
        return (
            <div className="flex h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-3 text-gray-500 font-medium">연동 상태를 불러오는 중...</span>
            </div>
        );
    }

    const connectors: Connector[] = connectorsData?.connectors || [];
    const activePlatformIds = activeConnections?.map((c: any) => c.platform) || [];

    const handleConnect = (connector: Connector) => {
        const apiKey = prompt(`${connector.name} API Key (또는 액세스 토큰)를 입력하세요:`);
        if (!apiKey) return;

        connectMutation.mutate({
            platformId: connector.id,
            creds: { api_key: apiKey }
        });
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">데이터 수집 센터</h1>
                <p className="text-gray-500">마케팅 채널을 연결하여 데이터를 자동으로 통합하세요.</p>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {connectors.map((connector: Connector) => {
                    const isConnected = activePlatformIds.includes(connector.id.toUpperCase());

                    return (
                        <DashboardWidget key={connector.id} title={connector.name}>
                            <div className="flex flex-col h-full">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className={clsx(
                                        "h-12 w-12 rounded-lg flex items-center justify-center border",
                                        connector.id === 'naver_ads' ? "bg-green-50 border-green-100 text-green-600" :
                                            connector.id === 'google_ads' ? "bg-blue-50 border-blue-100 text-blue-600" :
                                                "bg-indigo-50 border-indigo-100 text-indigo-600"
                                    )}>
                                        <Link2 className="h-6 w-6" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <h4 className="font-semibold text-gray-900">{connector.name}</h4>
                                            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                                                {connector.category}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1">
                                            {isConnected ? (
                                                <span className="flex items-center gap-1 text-[10px] text-primary font-bold">
                                                    <CheckCircle2 className="h-3 w-3" /> 연동됨 (ACTIVE)
                                                </span>
                                            ) : connector.status === 'AVAILABLE' ? (
                                                <span className="flex items-center gap-1 text-[10px] text-success font-bold">
                                                    <CheckCircle2 className="h-3 w-3" /> 연동 가능
                                                </span>
                                            ) : (
                                                <span className="flex items-center gap-1 text-[10px] text-amber-500 font-bold">
                                                    <AlertCircle className="h-3 w-3" /> 준비 중
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-500 mb-8 flex-1 leading-relaxed">
                                    {connector.description}
                                </p>

                                <button
                                    disabled={connector.status !== 'AVAILABLE' || isConnected || connectMutation.isPending}
                                    onClick={() => handleConnect(connector)}
                                    className={clsx(
                                        "flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all",
                                        (connector.status === 'AVAILABLE' && !isConnected)
                                            ? "bg-primary text-white hover:bg-opacity-90 shadow-sm active:scale-95"
                                            : "bg-gray-100 text-gray-400 cursor-not-allowed"
                                    )}
                                >
                                    {isConnected ? '이미 연결됨' : connectMutation.isPending ? '연결 중...' : connector.status === 'AVAILABLE' ? (
                                        <>연결하기 <ExternalLink className="h-4 w-4" /></>
                                    ) : (
                                        '준비 중'
                                    )}
                                </button>
                            </div>
                        </DashboardWidget>
                    );
                })}

                {/* Manual Upload Card */}
                <DashboardWidget title="CSV/Excel 업로드">
                    <div className="flex flex-col h-full opacity-60">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="h-12 w-12 rounded-lg bg-gray-50 flex items-center justify-center border border-gray-100">
                                <Link2 className="h-6 w-6 text-gray-400" />
                            </div>
                            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                                파일 업로드
                            </span>
                        </div>
                        <p className="text-sm text-gray-500 mb-8 flex-1">
                            API 연동이 불가능한 매체의 데이터를 파일 업로드 방식으로 직접 추가할 수 있습니다.
                        </p>
                        <button disabled className="bg-gray-100 text-gray-400 rounded-lg py-2.5 text-sm font-semibold cursor-not-allowed">
                            준비 중
                        </button>
                    </div>
                </DashboardWidget>
            </div>

            {notification && (
                <Notification
                    message={notification.message}
                    type={notification.type}
                    onClose={() => setNotification(null)}
                />
            )}
        </div>
    );
}
