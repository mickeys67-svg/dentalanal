import React from 'react';
import { FileText, Download, Share2, Calendar, CheckCircle2, Clock } from 'lucide-react';
import clsx from 'clsx';

interface ReportCardProps {
    title: string;
    date: string;
    status: 'COMPLETED' | 'SCHEDULED' | 'DRAFT';
    channels: string[];
}

export function ReportCard({ title, date, status, channels }: ReportCardProps) {
    return (
        <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-primary">
                    <FileText className="h-5 w-5" />
                </div>
                <div className={clsx(
                    "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                    status === 'COMPLETED' ? "bg-green-50 text-success" :
                        status === 'SCHEDULED' ? "bg-blue-50 text-blue-600" : "bg-gray-100 text-gray-500"
                )}>
                    {status}
                </div>
            </div>

            <div className="mt-4">
                <h4 className="font-semibold text-gray-900 line-clamp-1">{title}</h4>
                <div className="mt-1 flex items-center gap-1.5 text-xs text-gray-400">
                    <Calendar className="h-3 w-3" />
                    {date}
                </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
                {channels.map((channel) => (
                    <span key={channel} className="rounded bg-gray-50 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 border border-gray-100">
                        {channel}
                    </span>
                ))}
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-gray-50 pt-4">
                <div className="flex items-center gap-1 text-xs font-medium text-gray-500">
                    {status === 'COMPLETED' ? (
                        <><CheckCircle2 className="h-3 w-3 text-success" /> 공유 준비됨</>
                    ) : status === 'SCHEDULED' ? (
                        <><Clock className="h-3 w-3 text-blue-500" /> 발송 예정</>
                    ) : (
                        <><Clock className="h-3 w-3 text-gray-400" /> 초안</>
                    )}
                </div>
                <div className="flex gap-2">
                    <button className="rounded p-1.5 text-gray-400 hover:bg-gray-50 hover:text-primary transition-colors">
                        <Share2 className="h-4 w-4" />
                    </button>
                    <button className="rounded p-1.5 text-gray-400 hover:bg-gray-50 hover:text-primary transition-colors">
                        <Download className="h-4 w-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
