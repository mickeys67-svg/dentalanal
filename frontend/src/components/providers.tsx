'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { ClientProvider } from './providers/ClientProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <QueryClientProvider client={queryClient}>
            <ClientProvider>
                {children}
            </ClientProvider>
        </QueryClientProvider>
    );
}
