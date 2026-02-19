"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { queryAssistant, getAssistantQuickQueries } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import { EmptyClientPlaceholder } from '@/components/common/EmptyClientPlaceholder';
import ReactMarkdown from 'react-markdown';
import { Loader2, Send, Sparkles, MessageCircle, RotateCcw } from 'lucide-react';
import clsx from 'clsx';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    type?: string;
}

export default function AssistantPage() {
    const { selectedClient } = useClient();
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: '안녕하세요! **D-MIND AI 마케팅 어시스턴트**입니다.\n\n아래의 빠른 질문을 클릭하거나, 궁금한 것을 자유롭게 입력해 주세요.',
            type: 'markdown',
        },
    ]);
    const [input, setInput] = useState('');
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const { data: quickQueries = [] } = useQuery({
        queryKey: ['assistantQuickQueries'],
        queryFn: getAssistantQuickQueries,
    });

    const mutation = useMutation({
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
                { role: 'assistant', content: 'AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', type: 'text' },
            ]);
        },
    });

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, mutation.isPending]);

    const sendMessage = (query: string) => {
        if (!query.trim() || mutation.isPending) return;
        setMessages((prev) => [...prev, { role: 'user', content: query }]);
        setInput('');
        mutation.mutate({ query });
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const resetChat = () => {
        setMessages([
            {
                role: 'assistant',
                content: '대화가 초기화됐습니다. 다시 질문해 주세요!',
                type: 'markdown',
            },
        ]);
        setInput('');
    };

    return (
        <div className="flex flex-col h-[calc(100vh-64px)] max-w-4xl mx-auto px-4 py-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
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
                <button
                    onClick={resetChat}
                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                >
                    <RotateCcw className="w-3.5 h-3.5" /> 초기화
                </button>
            </div>

            {/* Quick Queries */}
            {quickQueries.length > 0 && (
                <div className="flex gap-2 flex-wrap mb-4">
                    {quickQueries.map((q) => (
                        <button
                            key={q.id}
                            onClick={() => sendMessage(q.id)}
                            disabled={mutation.isPending}
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

                {/* Loading indicator */}
                {mutation.isPending && (
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
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="궁금한 것을 자유롭게 입력하세요... (Enter로 전송, Shift+Enter 줄바꿈)"
                    rows={1}
                    className="flex-1 resize-none text-sm text-gray-800 placeholder-gray-400 bg-transparent outline-none leading-relaxed max-h-32 overflow-y-auto"
                    style={{ scrollbarWidth: 'none' }}
                    disabled={mutation.isPending}
                />
                <button
                    onClick={() => sendMessage(input)}
                    disabled={!input.trim() || mutation.isPending}
                    className="flex-shrink-0 w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    {mutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                </button>
            </div>

            <p className="text-center text-[10px] text-gray-300 mt-2">
                Powered by Gemini AI · 분석 결과는 참고용입니다
            </p>
        </div>
    );
}
