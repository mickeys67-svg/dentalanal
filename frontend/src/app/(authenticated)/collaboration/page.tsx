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
    takeApprovalAction,
    getTaskComments,
    createTaskComment,
    getNotices,
    createNotice
} from '@/lib/api';
import { CollaborativeTask, ApprovalRequest } from '@/types';
import { Notification, NotificationType } from '@/components/common/Notification';

import { Modal } from '@/components/common/Modal';
import { useClient } from '@/components/providers/ClientProvider';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';


export default function CollaborationPage() {
    const queryClient = useQueryClient();
    const { clients, selectedClient } = useClient();

    if (!selectedClient) {
        return <EmptyClientPlaceholder title="협업할 업체를 선택해주세요" description="업체를 선택하면 공지사항, 업무 현황 및 승인 요청을 관리할 수 있습니다." />;
    }
    const [notification, setNotification] = useState<{ message: string; type: NotificationType } | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [taskTitle, setTaskTitle] = useState('');
    const [taskOwner, setTaskOwner] = useState('박사원');
    const [targetClient, setTargetClient] = useState(selectedClient?.id || '');
    const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
    const [commentText, setCommentText] = useState('');

    // 1. Data Fetching
    const currentClientId = selectedClient?.id;
    const { data: tasks, isLoading: isTasksLoading } = useQuery({
        queryKey: ['collab-tasks', currentClientId],
        queryFn: () => getCollaborativeTasks(currentClientId!),
        enabled: !!currentClientId
    });

    const { data: approvals, isLoading: isApprovalsLoading } = useQuery({
        queryKey: ['approvals', currentClientId],
        queryFn: () => getApprovalRequests(currentClientId!),
        enabled: !!currentClientId
    });

    const { data: notices, isLoading: isNoticesLoading } = useQuery({
        queryKey: ['notices'],
        queryFn: () => getNotices()
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

    const { data: comments, isLoading: isCommentsLoading } = useQuery({
        queryKey: ['task-comments', selectedTaskId],
        queryFn: () => getTaskComments(selectedTaskId!),
        enabled: !!selectedTaskId
    });

    const commentMutation = useMutation({
        mutationFn: (content: string) => createTaskComment(selectedTaskId!, content),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['task-comments', selectedTaskId] });
            setCommentText('');
        }
    });

    const handleAddComment = () => {
        if (!commentText || !selectedTaskId) return;
        commentMutation.mutate(commentText);
    };

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
                    <h1 className="text-2xl font-bold text-foreground">영업 및 협업 센터</h1>
                    <p className="text-muted-foreground">팀과 프로젝트 간의 원활한 소통과 업무를 관리하세요.</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary">
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
                        <label htmlFor="modal-task-title" className="block text-sm font-medium text-foreground mb-1">업무 내용</label>
                        <input
                            id="modal-task-title"
                            name="title"
                            type="text"
                            className="w-full rounded-lg border-border text-sm focus:ring-primary focus:border-primary"
                            placeholder="할 일을 입력하세요"
                            value={taskTitle}
                            onChange={(e) => setTaskTitle(e.target.value)}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="modal-task-owner" className="block text-sm font-medium text-foreground mb-1">담당자</label>
                            <input
                                id="modal-task-owner"
                                name="owner"
                                type="text"
                                className="w-full rounded-lg border-border text-sm focus:ring-primary focus:border-primary"
                                value={taskOwner}
                                onChange={(e) => setTaskOwner(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="modal-task-client" className="block text-sm font-medium text-foreground mb-1">프로젝트</label>
                            <select
                                id="modal-task-client"
                                name="client_id"
                                className="w-full rounded-lg border-border text-sm focus:ring-primary focus:border-primary"
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
                            className="flex-1 px-4 py-2 border border-border text-muted-foreground rounded-lg text-sm font-medium hover:bg-secondary"
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
                    <DashboardWidget title="진행 중인 협업 업무" subtitle="팀원 및 프로젝트와 공유된 주요 과업입니다.">
                        <div className="space-y-3">
                            {isTasksLoading ? (
                                <div className="p-4 text-center text-muted-foreground">불러오는 중...</div>
                            ) : tasks && tasks.length > 0 ? (
                                tasks.map((task: CollaborativeTask) => (
                                    <div key={task.id} className="group flex items-center justify-between p-4 rounded-xl border border-border bg-card hover:border-primary/20 hover:shadow-sm transition-all">
                                        <div className="flex items-start gap-4">
                                            <div className={clsx(
                                                "mt-1 flex h-6 w-6 items-center justify-center rounded-full",
                                                task.status === 'COMPLETED' ? "bg-green-50 text-success" :
                                                    task.status === 'IN_PROGRESS' ? "bg-blue-50 text-blue-500" : "bg-background text-muted-foreground"
                                            )}>
                                                {task.status === 'COMPLETED' ? <CheckCircle2 className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-semibold text-foreground">{task.title}</h4>
                                                <div className="mt-1 flex items-center gap-3 text-[10px] text-muted-foreground">
                                                    <span className="font-bold text-muted-foreground uppercase">프로젝트</span>
                                                    <span>• 담당자: {task.owner || '미지정'}</span>
                                                    <span>• 기한: {task.deadline || '미정'}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => setSelectedTaskId(task.id)}
                                                className={clsx(
                                                    "p-1.5 rounded-lg transition-colors",
                                                    selectedTaskId === task.id ? "bg-primary text-white" : "text-muted-foreground hover:text-primary hover:bg-secondary"
                                                )}
                                                aria-label="채팅 및 피드백 확인"
                                                aria-pressed={selectedTaskId === task.id}
                                            >
                                                <MessageCircle className="h-4 w-4" aria-hidden="true" />
                                            </button>
                                            <button className="p-1.5 text-muted-foreground hover:text-primary"><ChevronRight className="h-4 w-4" /></button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-8 text-center text-muted-foreground border border-dashed rounded-xl">등록된 업무가 없습니다.</div>
                            )}
                        </div>
                    </DashboardWidget>

                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                        <DashboardWidget title="프로젝트 승인 요청">
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
                                            <p className="text-xs font-semibold text-foreground mb-3">{req.title}</p>
                                            {req.status === 'PENDING' && (
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleApproval(req.id, 'REJECTED')}
                                                        className="flex-1 bg-card text-[10px] font-bold py-1.5 rounded border border-amber-200 text-amber-700 hover:bg-amber-100 transition-colors"
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
                                    <div className="text-center py-4 text-muted-foreground text-xs">대기 중인 요청이 없습니다.</div>
                                )}
                            </div>
                        </DashboardWidget>
                        <DashboardWidget title="업무 피드백 / 실시간 소통">
                            {selectedTaskId ? (
                                <div className="flex flex-col h-[400px]">
                                    <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
                                        {isCommentsLoading ? (
                                            <div className="text-center py-10 text-muted-foreground">불러오는 중...</div>
                                        ) : comments && comments.length > 0 ? (
                                            comments.map((c: any) => (
                                                <div key={c.id} className="flex gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-primary/15 border border-primary flex items-center justify-center shrink-0">
                                                        <span className="text-[10px] font-bold text-primary">{c.user_name[0]}</span>
                                                    </div>
                                                    <div className="flex-1 bg-background rounded-2xl rounded-tl-none p-3 border border-border">
                                                        <div className="flex items-center justify-between mb-1">
                                                            <span className="text-[10px] font-bold text-foreground">{c.user_name}</span>
                                                            <span className="text-[9px] text-muted-foreground">{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                        </div>
                                                        <p className="text-xs text-muted-foreground leading-relaxed font-sans">{c.content}</p>
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-center py-20 bg-secondary rounded-xl border border-dashed border-border">
                                                <MessageSquare className="h-8 w-8 text-muted-foreground/60 mx-auto mb-2" />
                                                <p className="text-[10px] text-muted-foreground">첫 의견을 남겨보세요.</p>
                                            </div>
                                        )}
                                    </div>
                                    <div className="mt-auto relative">
                                        <textarea
                                            placeholder="메시지를 입력하세요..."
                                            className="w-full rounded-xl border-border focus:ring-primary focus:border-primary text-xs py-3 pl-4 pr-12 resize-none h-20 bg-secondary"
                                            value={commentText}
                                            onChange={(e) => setCommentText(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && !e.shiftKey) {
                                                    e.preventDefault();
                                                    handleAddComment();
                                                }
                                            }}
                                        />
                                        <button
                                            onClick={handleAddComment}
                                            disabled={!commentText || commentMutation.isPending}
                                            className="absolute right-3 bottom-3 p-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-all disabled:opacity-30"
                                        >
                                            <Plus className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
                                    <MessageCircle className="h-10 w-10 mb-4 opacity-20" />
                                    <p className="text-xs">업무를 선택하여 소통을 시작하세요.</p>
                                </div>
                            )}
                        </DashboardWidget>
                    </div>
                </div>

                {/* Client / Agency Hub */}
                <div className="space-y-6">
                    <DashboardWidget title="프로젝트 관리 현황">
                        <div className="relative mb-4">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                            <input type="text" placeholder="프로젝트 또는 브랜드 검색..." className="w-full pl-10 pr-4 py-2 text-xs border border-border rounded-lg focus:outline-none focus:border-primary" />
                        </div>
                        <div className="space-y-4">
                            {clients.map((client, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary transition-colors cursor-pointer border border-transparent hover:border-border">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "h-2 w-2 rounded-full",
                                            "bg-success"
                                        )}></div>
                                        <div>
                                            <p className="text-sm font-semibold text-foreground">{client.name}</p>
                                            <p className="text-[10px] text-muted-foreground">데이터 동기화 완료</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs font-bold text-foreground">90%</p>
                                        <p className="text-[8px] text-muted-foreground uppercase font-bold tracking-tighter">Health Score</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </DashboardWidget>

                    <DashboardWidget title="팀 활동 로그">
                        <div className="space-y-4">
                            {[
                                { icon: CheckSquare, msg: '리포트를 발송했습니다.', time: '5분 전' },
                                { icon: Bell, msg: `${selectedClient.name}에서 예산을 승인했습니다.`, time: '1시간 전' },
                                { icon: Lightbulb, msg: 'AI 전략이 업데이트 되었습니다.', time: '3시간 전' },
                            ].map((log, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <log.icon className="h-3.5 w-3.5 text-muted-foreground/60 mt-0.5" />
                                    <div>
                                        <p className="text-[11px] text-muted-foreground leading-tight">{log.msg}</p>
                                        <p className="text-[9px] text-muted-foreground mt-1">{log.time}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </DashboardWidget>
                </div>
            </div>

            {/* Notice Board Section */}
            <div className="mt-12 bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
                <div className="p-6 border-b border-border flex items-center justify-between bg-secondary">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary text-white rounded-lg">
                            <Bell className="h-5 w-5" />
                        </div>
                        <div>
                            <h3 className="font-bold text-foreground">전사 공지 및 업무 가이드</h3>
                            <p className="text-xs text-muted-foreground">마케팅팀 및 내부 인원 전체 공유 게시판</p>
                        </div>
                    </div>
                </div>
                <div className="divide-y divide-border">
                    {isNoticesLoading ? (
                        <div className="p-10 text-center text-muted-foreground text-xs">공지사항을 불러오는 중...</div>
                    ) : notices && notices.length > 0 ? (
                        notices.map((notice: any) => (
                            <div key={notice.id} className="p-4 hover:bg-secondary transition-colors cursor-pointer group">
                                <div className="flex items-center gap-3">
                                    {notice.is_pinned && <span className="px-2 py-0.5 bg-red-50 text-red-500 text-[10px] font-bold rounded border border-red-100">PINNED</span>}
                                    <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{notice.title}</h4>
                                    <span className="text-[10px] text-muted-foreground ml-auto">작성자: {notice.author_name} • {new Date(notice.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="p-10 text-center text-muted-foreground text-xs">등록된 공지사항이 없습니다.</div>
                    )}
                </div>
                <div className="p-4 bg-background text-center">
                    <button className="text-xs font-bold text-primary hover:underline">전체 게시글 보기</button>
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
