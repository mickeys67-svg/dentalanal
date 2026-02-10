"use client";

import React, { useEffect } from 'react';
import { CheckCircle, AlertCircle, X, Info } from 'lucide-react';
import clsx from 'clsx';

export type NotificationType = 'SUCCESS' | 'ERROR' | 'INFO' | 'WARNING';

interface NotificationProps {
    message: string;
    type: NotificationType;
    onClose: () => void;
    duration?: number;
}

export const Notification: React.FC<NotificationProps> = ({ message, type, onClose, duration = 3000 }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose();
        }, duration);
        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const icons = {
        SUCCESS: <CheckCircle className="h-5 w-5 text-success" />,
        ERROR: <AlertCircle className="h-5 w-5 text-red-500" />,
        INFO: <Info className="h-5 w-5 text-indigo-500" />,
        WARNING: <AlertCircle className="h-5 w-5 text-amber-500" />,
    };

    const styles = {
        SUCCESS: "bg-success/10 border-success/20",
        ERROR: "bg-red-50 border-red-100",
        INFO: "bg-indigo-50 border-indigo-100",
        WARNING: "bg-amber-50 border-amber-100",
    };

    return (
        <div className={clsx(
            "fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg animate-in slide-in-from-right-full duration-300",
            styles[type]
        )}>
            {icons[type]}
            <p className="text-sm font-medium text-gray-800">{message}</p>
            <button onClick={onClose} className="p-1 hover:bg-black/5 rounded-full transition-colors">
                <X className="h-4 w-4 text-gray-400" />
            </button>
        </div>
    );
};
