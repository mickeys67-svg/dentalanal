"use client";

import { useClient } from "@/components/providers/ClientProvider";
import { useAuth } from "@/components/providers/AuthProvider";
import { LogOut, User } from "lucide-react";

export function Header() {
    const { clients, selectedClient, setSelectedClient } = useClient();
    const { user, logout } = useAuth();

    return (
        <header className="bg-white border-b border-gray-100 h-16 flex items-center shrink-0">
            <div className="w-full max-w-7xl mx-auto px-6 flex justify-between items-center">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-bold text-gray-900">통합 분석 솔루션</h1>
                    <div className="h-6 w-px bg-gray-200"></div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">업체:</span>
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
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3 border-r border-gray-100 pr-6">
                        <div className="flex flex-col items-end">
                            <span className="text-sm font-bold text-gray-900">{user?.name || '사용자'}님</span>
                            <span className="text-[10px] text-primary font-bold tracking-tighter uppercase">{user?.role} 권한</span>
                        </div>
                        <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-sm ring-2 ring-white shadow-sm">
                            <User className="w-5 h-5" />
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="flex items-center gap-2 text-gray-400 hover:text-red-500 transition-colors text-xs font-bold"
                        title="로그아웃"
                    >
                        <LogOut className="w-4 h-4" />
                        로그아웃
                    </button>
                </div>
            </div>
        </header>
    );
}
