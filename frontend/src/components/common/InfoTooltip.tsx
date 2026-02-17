'use client';

import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { Modal } from './Modal';

interface InfoTooltipProps {
    title: string;
    content: string;
}

export function InfoTooltip({ title, content }: InfoTooltipProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="inline-block ml-2 align-middle">
            <button
                onClick={(e) => {
                    e.preventDefault();
                    setIsOpen(true);
                }}
                className="text-gray-300 hover:text-indigo-500 transition-colors"
                title={`${title} 정보`}
            >
                <HelpCircle className="w-4 h-4 cursor-pointer" />
            </button>

            <Modal
                isOpen={isOpen}
                onClose={() => setIsOpen(false)}
                title={title}
            >
                <div className="p-6">
                    <p className="text-gray-600 leading-relaxed text-sm whitespace-pre-line">
                        {content}
                    </p>
                    <div className="mt-6 flex justify-end">
                        <button
                            onClick={() => setIsOpen(false)}
                            className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 px-6 rounded-xl transition-all"
                        >
                            닫기
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
