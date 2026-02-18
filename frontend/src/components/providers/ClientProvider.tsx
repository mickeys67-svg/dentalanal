'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Client } from '@/types';
import { getClients } from '@/lib/api';
import { useAuth } from './AuthProvider';

interface ClientContextType {
    clients: Client[];
    selectedClient: Client | null;
    setSelectedClient: (client: Client) => void;
    isLoading: boolean;
    refreshClients: () => Promise<void>;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

export function ClientProvider({ children }: { children: React.ReactNode }) {
    const { user, isLoading: isAuthLoading } = useAuth();
    const [clients, setClients] = useState<Client[]>([]);
    const [selectedClient, setSelectedClient] = useState<Client | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshClients = useCallback(async () => {
        if (!user) {
            setClients([]);
            setSelectedClient(null);
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            const data = await getClients();
            setClients(data);

            // Restore from localStorage or pick first
            const savedId = localStorage.getItem('selectedClientId');
            const savedClient = data.find(c => c.id === savedId);

            if (data.length > 0) {
                setSelectedClient(savedClient ?? data[0]);
            } else {
                setSelectedClient(null);
            }
        } catch (error) {
            console.error('Failed to fetch clients:', error);
            setClients([]);
            setSelectedClient(null);
        } finally {
            setIsLoading(false);
        }
    // selectedClient를 deps에서 제거 - 무한루프 방지
    }, [user]);

    useEffect(() => {
        if (!isAuthLoading) {
            refreshClients();
        }
    }, [isAuthLoading, refreshClients]);

    useEffect(() => {
        if (selectedClient) {
            localStorage.setItem('selectedClientId', selectedClient.id);
        }
    }, [selectedClient]);

    return (
        <ClientContext.Provider value={{
            clients,
            selectedClient,
            setSelectedClient,
            isLoading,
            refreshClients
        }}>
            {children}
        </ClientContext.Provider>
    );
}

export function useClient() {
    const context = useContext(ClientContext);
    if (context === undefined) {
        throw new Error('useClient must be used within a ClientProvider');
    }
    return context;
}
