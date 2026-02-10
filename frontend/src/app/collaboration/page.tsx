"use client";

import React, { useState } from 'react';
import { DashboardWidget } from '@/components/dashboard/DashboardWidget';
import {
    Users,
    CheckSquare,
    MessageSquare,
    Bell,
    UserPlus,
    Clock,
    CheckCircle2,
    AlertCircle,
    ChevronRight,
    Search,
    MessageCircle,
    Lightbulb,
    Plus
} from 'lucide-react';
import clsx from 'clsx';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getCollaborativeTasks,
    createCollaborativeTask,
    getApprovalRequests,
    takeApprovalAction
} from '@/lib/api';
import { CollaborativeTask, ApprovalRequest } from '@/types';
import { Notification, NotificationType } from '@/components/common/Notification';

import { Modal } from '@/components/common/Modal';
import { useClient } from '@/components/providers/ClientProvider';

const DEFAULT_CLIENT_ID = "00000000-0000-0000-0000-000000000000"; // Placeholder

const mockClients = [
    { name: 'A 치과', score: 85, status: 'Active', tasks: 3 },
    { name: 'B 의원', score: 92, status: 'Active', tasks: 1 },
    { name: 'C 메디컬', score: 78, status: 'Warning', tasks: 5 },
];

export default function CollaborationPage() {
    const queryClient = useQueryClient();
    const { clients, selectedClient } = useClient();
    const [notification, setNotification] = useState<{ message: string; type: NotificationType } | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [taskTitle, setTaskTitle] = useState('');
    const [taskOwner, setTaskOwner] = useState('박사원');
    const [targetClient, setTargetClient] = useState(selectedClient?.id || DEFAULT_CLIENT_ID);

    // 1. Data Fetching
    const currentClientId = selectedClient?.id || DEFAULT_CLIENT_ID;
    const { data: tasks, isLoading: isTasksLoading } = useQuery({
        queryKey: ['collab-tasks', currentClientId],
        queryFn: () => getCollaborativeTasks(currentClientId)
    });

    const { data: approvals, isLoading: isApprovalsLoading } = useQuery({
        queryKey: ['approvals', currentClientId],
        queryFn: () => getApprovalRequests(currentClientId)
    });

    // 2. Mutations
    const taskMutation = useMutation({
        mutationFn: (data: Partial<CollaborativeTask>) => createCollaborativeTask(targetClient, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collab-tasks'] });
            setNotification({ message: "새 업무가 등록되었습니다.", type: 'SUCCESS' });
            setIsModalOpen(false);
            setTaskTitle('');
        }
    });

    const approvalMutation = useMutation({
        mutationFn: ({ id, action }: { id: string, action: 'APPROVED' | 'REJECTED' }) =>
            takeApprovalAction(id, action),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['approvals'] });
            setNotification({ message: "승인 요청이 처리되었습니다.", type: 'SUCCESS' });
        }
    });

    const handleAddTask = () => {
        if (!taskTitle) return;
        taskMutation.mutate({ title: taskTitle, status: 'PENDING', owner: taskOwner });
    };

    const handleApproval = (id: string, action: 'APPROVED' | 'REJECTED') => {
        approvalMutation.mutate({ id, action });
    };

    return (
        <div className="space-y-8 p-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">영업 및 협업 센터</h1>
                    <p className="text-gray-500">대행사와 광고주 간의 원활환 소통과 업무를 관리하세요.</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                        <UserPlus className="h-4 w-4" /> 팀원 초대
                    </button>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-opacity-90 shadow-sm"
                    >
                        <Plus className="h-4 w-4" /> 새 업무 등록
                    </button>
                </div>
            </div>

            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="새 업무 등록"
            >
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">업무 내용</label>
                        <input
                            type="text"
                            className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                            placeholder="할 일을 입력하세요"
                            value={taskTitle}
                            onChange={(e) => setTaskTitle(e.target.value)}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">담당자</label>
                            <input
                                type="text"
                                className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                                value={taskOwner}
                                onChange={(e) => setTaskOwner(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">광고주</label>
                            <select
                                className="w-full rounded-lg border-gray-200 text-sm focus:ring-primary focus:border-primary"
                                value={targetClient}
                                onChange={(e) => setTargetClient(e.target.value)}
                            >
                                {clients.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="pt-4 flex gap-3">
                        <button
                            onClick={() => setIsModalOpen(false)}
                            className="flex-1 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-50"
                        >취소</button>
                        <button
                            onClick={handleAddTask}
                            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark shadow-md"
                        >등록하기</button>
                    </div>
                </div>
            </Modal>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Task Management Section */}
                <div className="lg:col-span-2 space-y-6">
                    <DashboardWidget title="진행 중인 협업 업무" subtitle="팀원 및 광고주와 공유된 주요 과업입니다.">
                        <div className="space-y-3">
                            {isTasksLoading ? (
                                <div className="p-4 text-center text-gray-400">불러오는 중...</div>
                            ) : tasks && tasks.length > 0 ? (
                                tasks.map((task: CollaborativeTask) => (
                                    <div key={task.id} className="group flex items-center justify-between p-4 rounded-xl border border-gray-50 bg-white hover:border-primary/20 hover:shadow-sm transition-all">
                                        <div className="flex items-start gap-4">
                                            <div className={clsx(
                                                "mt-1 flex h-6 w-6 items-center justify-center rounded-full",
                                                task.status === 'COMPLETED' ? "bg-green-50 text-success" :
                                                    task.status === 'IN_PROGRESS' ? "bg-blue-50 text-blue-500" : "bg-gray-50 text-gray-400"
                                            )}>
                                                {task.status === 'COMPLETED' ? <CheckCircle2 className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-900">{task.title}</h4>
                                                <div className="mt-1 flex items-center gap-3 text-[10px] text-gray-400">
                                                    <span className="font-bold text-gray-500 uppercase">광고주</span>
                                                    <span>• 담당자: {task.owner || '미지정'}</span>
                                                    <span>• 기한: {task.deadline || '미정'}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button className="p-1.5 text-gray-400 hover:text-primary"><MessageCircle className="h-4 w-4" /></button>
                                            <button className="p-1.5 text-gray-400 hover:text-primary"><ChevronRight className="h-4 w-4" /></button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-8 text-center text-gray-400 border border-dashed rounded-xl">등록된 업무가 없습니다.</div>
                            )}
                        </div>
                    </DashboardWidget>

                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                        <DashboardWidget title="광고주 승인 요청">
                            <div className="space-y-4">
                                {approvals && approvals.length > 0 ? (
                                    approvals.map((req: ApprovalRequest) => (
                                        <div key={req.id} className={clsx(
                                            "p-4 rounded-xl border",
                                            req.status === 'PENDING' ? "bg-amber-50 border-amber-100" :
                                                req.status === 'APPROVED' ? "bg-green-50 border-green-100" : "bg-red-50 border-red-100"
                                        )}>
                                            <div className="flex items-center justify-between mb-2">
                                                <span className={clsx(
                                                    "text-[10px] font-bold uppercase",
                                                    req.status === 'PENDING' ? "text-amber-700" :
                                                        req.status === 'APPROVED' ? "text-success" : "text-red-700"
                                                )}>{req.request_type || '요청'} • {req.status}</span>
                                            </div>
                                            <p className="text-xs font-semibold text-gray-800 mb-3">{req.title}</p>
                                            {req.status === 'PENDING' && (
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleApproval(req.id, 'REJECTED')}
                                                        className="flex-1 bg-white text-[10px] font-bold py-1.5 rounded border border-amber-200 text-amber-700 hover:bg-amber-100 transition-colors"
                                                    >거절</button>
                                                    <button
                                                        onClick={() => handleApproval(req.id, 'APPROVED')}
                                                        className="flex-1 bg-amber-500 text-[10px] font-bold py-1.5 rounded text-white hover:bg-amber-600 transition-colors"
                                                    >승인하기</button>
                                                </div>
                                            )}
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-4 text-gray-400 text-xs">대기 중인 요청이 없습니다.</div>
                                )}
                            </div>
                        </DashboardWidget>
                        <DashboardWidget title="최근 커뮤니케이션">
                            <div className="space-y-4">
                                {[1, 2].map(i => (
                                    <div key={i} className="flex gap-3">
                                        <div className="h-8 w-8 rounded-full bg-gray-100 shrink-0"></div>
                                        <div>
                                            <p className="text-xs font-semibold text-gray-900">이팀장 <span className="text-[10px] font-normal text-gray-400 ml-1">10분 전</span></p>
                                            <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-1">네이버 광고 소재 수정했습니다. 확인 부탁드립...</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </DashboardWidget>
                    </div>
                </div>

                {/* Client / Agency Hub */}
                <div className="space-y-6">
                    <DashboardWidget title="광고주 관리 현황">
                        <div className="relative mb-4">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                            <input type="text" placeholder="광고주 또는 브랜드 검색..." className="w-full pl-10 pr-4 py-2 text-xs border border-gray-100 rounded-lg focus:outline-none focus:border-primary" />
                        </div>
                        <div className="space-y-4">
                            {mockClients.map((client, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer border border-transparent hover:border-gray-100">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "h-2 w-2 rounded-full",
                                            client.status === 'Active' ? "bg-success" : "bg-amber-400"
                                        )}></div>
                                        <div>
                                            <p className="text-sm font-semibold text-gray-900">{client.name}</p>
                                            <p className="text-[10px] text-gray-400">{client.tasks}개 업무 진행 중</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs font-bold text-gray-900">{client.score}%</p>
                                        <p className="text-[8px] text-gray-400 uppercase font-bold tracking-tighter">Heath Score</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </DashboardWidget>

                    <DashboardWidget title="팀 활동 로그">
                        <div className="space-y-4">
                            {[
                                { icon: CheckSquare, msg: '박사원이 리포트를 발송했습니다.', time: '5분 전' },
                                { icon: Bell, msg: 'A치과에서 예산을 승인했습니다.', time: '1시간 전' },
                                { icon: Lightbulb, msg: 'AI 전략이 업데이트 되었습니다.', time: '3시간 전' },
                            ].map((log, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <log.icon className="h-3.5 w-3.5 text-gray-300 mt-0.5" />
                                    <div>
                                        <p className="text-[11px] text-gray-600 leading-tight">{log.msg}</p>
                                        <p className="text-[9px] text-gray-400 mt-1">{log.time}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </DashboardWidget>
                </div>
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
