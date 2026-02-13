"use client";

import React from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl';
}

export function Modal({ isOpen, onClose, title, children, maxWidth = 'lg' }: ModalProps) {
    if (!isOpen) return null;

    const maxWidthClass = {
        'sm': 'max-w-sm',
        'md': 'max-w-md',
        'lg': 'max-w-lg',
        'xl': 'max-w-xl',
        '2xl': 'max-w-2xl',
        '3xl': 'max-w-3xl',
        '4xl': 'max-w-4xl',
        '5xl': 'max-w-5xl',
    }[maxWidth];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
            <div className={clsx(
                "bg-white rounded-3xl shadow-2xl w-full flex flex-col overflow-hidden animate-in zoom-in-95 duration-300 max-h-[90vh]",
                maxWidthClass
            )}>
                <div className="flex items-center justify-between p-7 border-b border-gray-100 shrink-0">
                    <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-all active:scale-90"
                    >
                        <X className="w-6 h-6 text-gray-400" />
                    </button>
                </div>
                <div className="p-8 overflow-y-auto custom-scrollbar">
                    {children}
                </div>
            </div>
        </div>
    );
}
