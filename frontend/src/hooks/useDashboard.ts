import { useQuery, useMutation } from '@tanstack/react-query';
import { getDashboardSummary, triggerSync } from '@/lib/api';

export function useDashboard(clientId?: string) {
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['dashboardSummary', clientId],
        queryFn: () => getDashboardSummary(clientId),
        staleTime: 5 * 60 * 1000,
    });

    const syncMutation = useMutation({
        mutationFn: triggerSync,
        onSuccess: () => {
            // Refetch dashboard data after a short delay or immediately
            setTimeout(() => refetch(), 2000);
        }
    });

    return {
        summary: data,
        isLoading,
        error,
        isSyncing: syncMutation.isPending,
        refresh: refetch,
        startSync: () => syncMutation.mutate()
    };
}
