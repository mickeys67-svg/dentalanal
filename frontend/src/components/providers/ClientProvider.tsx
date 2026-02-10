'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Client } from '@/types';
import { getClients } from '@/lib/api';

interface ClientContextType {
    clients: Client[];
    selectedClient: Client | null;
    setSelectedClient: (client: Client) => void;
    isLoading: boolean;
    refreshClients: () => Promise<void>;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

export function ClientProvider({ children }: { children: React.ReactNode }) {
    const [clients, setClients] = useState<Client[]>([]);
    const [selectedClient, setSelectedClient] = useState<Client | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshClients = async () => {
        try {
            const data = await getClients();
            setClients(data);
            if (data.length > 0 && !selectedClient) {
                // Restore from localStorage or pick first
                const savedId = localStorage.getItem('selectedClientId');
                const savedClient = data.find(c => c.id === savedId);
                setSelectedClient(savedClient || data[0]);
            }
        } catch (error) {
            console.error('Failed to fetch clients:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        refreshClients();
    }, []);

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
