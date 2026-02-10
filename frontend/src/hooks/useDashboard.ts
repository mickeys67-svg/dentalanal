import { useQuery, useMutation } from '@tanstack/react-query';
import { getDashboardSummary, triggerSync } from '@/lib/api';

export function useDashboard(clientId?: string | null) {
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['dashboardSummary', clientId],
        queryFn: () => getDashboardSummary(clientId || undefined),
        staleTime: 5 * 60 * 1000,
        enabled: true, // Always allow fetching, but backend handles empty
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
