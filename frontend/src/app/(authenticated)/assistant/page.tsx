"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    queryAssistant, streamAssistantQuery, getAssistantQuickQueries,
    getChatSessions, getChatSessionMessages, deleteChatSession,
    type ChatSession,
} from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import ReactMarkdown from 'react-markdown';
import {
    Loader2, Send, Sparkles, MessageCircle, RotateCcw,
    History, Trash2, PanelLeft, Plus,
} from 'lucide-react';
import clsx from 'clsx';

interface LocalMessage {
    role: 'user' | 'assistant';
    content: string;
    type?: string;
    streaming?: boolean;
}

const WELCOME: LocalMessage = {
    role: 'assistant',
    content: '안녕하세요! **D-MIND AI 마케팅 어시스턴트**입니다.\n\n아래의 빠른 질문을 클릭하거나, 궁금한 것을 자유롭게 입력해 주세요.',
    type: 'markdown',
};

export default function AssistantPage() {
    const { selectedClient } = useClient();
    const queryClient = useQueryClient();

    const [showHistory, setShowHistory] = useState(false);
    const [activeSessionId, setActiveSessionId] = useState<string | undefined>(undefined);
    const [messages, setMessages] = useState<LocalMessage[]>([WELCOME]);
    const [input, setInput] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const stopStreamRef = useRef<(() => void) | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    const { data: quickQueries = [] } = useQuery({
        queryKey: ['assistantQuickQueries'],
        queryFn: getAssistantQuickQueries,
    });

    const { data: sessions = [] } = useQuery({
        queryKey: ['chatSessions'],
        queryFn: getChatSessions,
        enabled: showHistory,
    });

    const quickMutation = useMutation({
        mutationFn: ({ query }: { query: string }) =>
            queryAssistant(query, selectedClient?.id),
        onSuccess: (data) => {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: data.report, type: data.type },
            ]);
        },
        onError: () => {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: 'AI 응답 중 오류가 발생했습니다.', type: 'text' },
            ]);
        },
    });

    const deleteSessionMutation = useMutation({
        mutationFn: deleteChatSession,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chatSessions'] }),
    });

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isStreaming]);

    const sendStreamMessage = useCallback((query: string) => {
        if (!query.trim() || isStreaming) return;
        setMessages((prev) => [...prev, { role: 'user', content: query }]);
        setInput('');
        setIsStreaming(true);
        setMessages((prev) => [...prev, { role: 'assistant', content: '', type: 'markdown', streaming: true }]);

        const stop = streamAssistantQuery(
            query,
            selectedClient?.id,
            activeSessionId,
            (delta) => {
                setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last?.streaming) {
                        next[next.length - 1] = { ...last, content: last.content + delta };
                    }
                    return next;
                });
            },
            (sessionId) => {
                setIsStreaming(false);
                stopStreamRef.current = null;
                if (sessionId && !activeSessionId) setActiveSessionId(sessionId);
                setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last?.streaming) next[next.length - 1] = { ...last, streaming: false };
                    return next;
                });
                queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
            },
            (err) => {
                setIsStreaming(false);
                stopStreamRef.current = null;
                setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last?.streaming) {
                        next[next.length - 1] = { role: 'assistant', content: `오류: ${err}`, type: 'text', streaming: false };
                    }
                    return next;
                });
            },
        );
        stopStreamRef.current = stop;
    }, [isStreaming, selectedClient?.id, activeSessionId, queryClient]);

    const sendQuickQuery = useCallback((queryId: string) => {
        if (isStreaming || quickMutation.isPending) return;
        setMessages((prev) => [...prev, { role: 'user', content: queryId }]);
        quickMutation.mutate({ query: queryId });
    }, [isStreaming, quickMutation]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendStreamMessage(input);
        }
    };

    const resetChat = () => {
        if (isStreaming) stopStreamRef.current?.();
        setMessages([WELCOME]);
        setInput('');
        setIsStreaming(false);
        setActiveSessionId(undefined);
    };

    const loadSession = async (session: ChatSession) => {
        try {
            const data = await getChatSessionMessages(session.id);
            const loaded: LocalMessage[] = data.messages.map((m) => ({
                role: m.role as 'user' | 'assistant',
                content: m.content,
                type: m.msg_type,
            }));
            setMessages(loaded.length ? loaded : [WELCOME]);
            setActiveSessionId(session.id);
            setShowHistory(false);
        } catch {
            setMessages([WELCOME]);
        }
    };

    const isPending = isStreaming || quickMutation.isPending;

    return (
        <div className="flex h-[calc(100vh-64px)]">
            {/* History Sidebar */}
            {showHistory && (
                <div className="w-64 flex-shrink-0 bg-gray-50 border-r border-gray-100 flex flex-col">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                        <span className="text-sm font-bold text-gray-700">대화 기록</span>
                        <button
                            onClick={() => { resetChat(); setShowHistory(false); }}
                            className="flex items-center gap-1 text-xs text-indigo-600 font-semibold hover:underline"
                        >
                            <Plus className="w-3.5 h-3.5" /> 새 대화
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto py-2">
                        {sessions.length === 0 ? (
                            <p className="text-xs text-gray-400 text-center mt-8">저장된 대화가 없습니다.</p>
                        ) : (
                            sessions.map((s) => (
                                <div
                                    key={s.id}
                                    className={clsx(
                                        'group flex items-center justify-between px-4 py-2.5 cursor-pointer hover:bg-white transition-colors text-sm',
                                        s.id === activeSessionId ? 'bg-white font-bold text-indigo-700' : 'text-gray-600'
                                    )}
                                    onClick={() => loadSession(s)}
                                >
                                    <span className="truncate flex-1">{s.title || '(제목 없음)'}</span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteSessionMutation.mutate(s.id);
                                            if (s.id === activeSessionId) resetChat();
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-300 hover:text-red-400 transition-all flex-shrink-0"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Main Chat */}
            <div className="flex flex-col flex-1 min-w-0 max-w-4xl mx-auto px-4 py-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setShowHistory((v) => !v)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-gray-700"
                            title="대화 기록"
                        >
                            <PanelLeft className="w-4 h-4" />
                        </button>
                        <div className="p-2.5 bg-indigo-600 rounded-xl shadow-md shadow-indigo-600/20">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">AI 마케팅 어시스턴트</h1>
                            <p className="text-xs text-gray-400">
                                {selectedClient
                                    ? `${selectedClient.name} 데이터 기반 분석`
                                    : '업체를 선택하면 데이터 기반 답변이 가능합니다'}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {activeSessionId && (
                            <span className="text-[10px] bg-indigo-50 text-indigo-500 font-semibold px-2 py-1 rounded-full border border-indigo-100 flex items-center gap-1">
                                <History className="w-3 h-3" /> 저장됨
                            </span>
                        )}
                        <button
                            onClick={resetChat}
                            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                            <RotateCcw className="w-3.5 h-3.5" /> 초기화
                        </button>
                    </div>
                </div>

                {/* Quick Queries */}
                {quickQueries.length > 0 && (
                    <div className="flex gap-2 flex-wrap mb-4">
                        {quickQueries.map((q) => (
                            <button
                                key={q.id}
                                onClick={() => sendQuickQuery(q.id)}
                                disabled={isPending}
                                className="px-3 py-1.5 text-xs font-semibold bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100 hover:bg-indigo-100 transition-colors disabled:opacity-40"
                                title={q.description}
                            >
                                {q.label}
                            </button>
                        ))}
                    </div>
                )}

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={clsx(
                                'flex gap-3',
                                msg.role === 'user' ? 'justify-end' : 'justify-start'
                            )}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                            )}
                            <div
                                className={clsx(
                                    'max-w-[80%] rounded-2xl px-5 py-4 text-sm leading-relaxed',
                                    msg.role === 'user'
                                        ? 'bg-indigo-600 text-white rounded-tr-sm'
                                        : 'bg-white border border-gray-100 shadow-sm text-gray-800 rounded-tl-sm'
                                )}
                            >
                                {msg.role === 'assistant' && msg.type === 'markdown' ? (
                                    <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900">
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                        {msg.streaming && (
                                            <span className="inline-block w-1.5 h-4 bg-indigo-500 ml-0.5 animate-pulse rounded-sm align-middle" />
                                        )}
                                    </div>
                                ) : (
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                )}
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <MessageCircle className="w-4 h-4 text-gray-500" />
                                </div>
                            )}
                        </div>
                    ))}

                    {quickMutation.isPending && (
                        <div className="flex gap-3 justify-start">
                            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                                <Sparkles className="w-4 h-4 text-white" />
                            </div>
                            <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-5 py-4">
                                <div className="flex items-center gap-2 text-gray-400 text-sm">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>AI가 분석 중입니다...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-3 flex items-end gap-3">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="궁금한 것을 자유롭게 입력하세요... (Enter로 전송, Shift+Enter 줄바꿈)"
                        rows={1}
                        className="flex-1 resize-none text-sm text-gray-800 placeholder-gray-400 bg-transparent outline-none leading-relaxed max-h-32 overflow-y-auto"
                        style={{ scrollbarWidth: 'none' }}
                        disabled={isPending}
                    />
                    <button
                        onClick={() => isStreaming ? stopStreamRef.current?.() : sendStreamMessage(input)}
                        disabled={!isStreaming && !input.trim()}
                        className={clsx(
                            'flex-shrink-0 w-9 h-9 rounded-xl text-white flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
                            isStreaming ? 'bg-red-500 hover:bg-red-600' : 'bg-indigo-600 hover:bg-indigo-700'
                        )}
                        title={isStreaming ? '스트리밍 중단' : '전송'}
                    >
                        {isStreaming ? (
                            <span className="w-3 h-3 bg-white rounded-sm" />
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                    </button>
                </div>

                <p className="text-center text-[10px] text-gray-300 mt-2">
                    Powered by Gemini AI · 분석 결과는 참고용입니다
                </p>
            </div>
        </div>
    );
}
