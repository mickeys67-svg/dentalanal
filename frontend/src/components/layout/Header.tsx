"use client";

import { useClient } from "@/components/providers/ClientProvider";

export function Header() {
    const { clients, selectedClient, setSelectedClient } = useClient();

    return (
        <header className="bg-white border-b border-gray-100 h-16 flex items-center shrink-0">
            <div className="w-full max-w-7xl mx-auto px-6 flex justify-between items-center">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-bold text-gray-900">대시보드</h1>
                    <div className="h-6 w-px bg-gray-200"></div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">현재 관리 업체:</span>
                        <select
                            value={selectedClient?.id || ""}
                            onChange={(e) => {
                                const client = clients.find(c => c.id === e.target.value);
                                if (client) setSelectedClient(client);
                            }}
                            className="text-sm font-semibold border-none bg-gray-50 rounded-md px-2 py-1 focus:ring-0 cursor-pointer text-primary"
                        >
                            {clients.length === 0 && <option value="">업체 없음</option>}
                            {clients.map(client => (
                                <option key={client.id} value={client.id}>
                                    {client.name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end">
                        <span className="text-sm font-bold text-gray-900">관리자님</span>
                        <span className="text-[10px] text-gray-400">마스터 권한</span>
                    </div>
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xs ring-2 ring-white">
                        AD
                    </div>
                </div>
            </div>
        </header>
    );
}
