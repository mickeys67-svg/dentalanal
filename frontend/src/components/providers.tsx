'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { ClientProvider } from './providers/ClientProvider';
import { AuthProvider } from './providers/AuthProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <ClientProvider>
                    {children}
                </ClientProvider>
            </AuthProvider>
        </QueryClientProvider>
    );
}
