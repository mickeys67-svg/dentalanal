import { useQuery, useMutation } from '@tanstack/react-query';
import { getDashboardSummary, getMetricsTrend, triggerSync, scrapePlace, scrapeView } from '@/lib/api';

export function useDashboard(clientId?: string | null) {
    const { data: summary, isLoading: isSummaryLoading, error: summaryError, refetch: refetchSummary } = useQuery({
        queryKey: ['dashboardSummary', clientId],
        queryFn: () => getDashboardSummary(clientId || undefined),
        staleTime: 5 * 60 * 1000,
    });

    const { data: trend, isLoading: isTrendLoading, refetch: refetchTrend } = useQuery({
        queryKey: ['dashboardTrend', clientId],
        queryFn: () => getMetricsTrend(clientId || undefined),
        staleTime: 5 * 60 * 1000,
    });

    const syncMutation = useMutation({
        mutationFn: triggerSync,
        onSuccess: () => {
            setTimeout(() => {
                refetchSummary();
                refetchTrend();
            }, 2000);
        }
    });

    const placeMutation = useMutation({
        mutationFn: (keyword: string) => scrapePlace(keyword),
        onSuccess: () => refetchSummary()
    });

    const viewMutation = useMutation({
        mutationFn: (keyword: string) => scrapeView(keyword),
        onSuccess: () => refetchSummary()
    });

    return {
        summary,
        trend,
        isLoading: isSummaryLoading || isTrendLoading,
        error: summaryError,
        isSyncing: syncMutation.isPending,
        isPlacePending: placeMutation.isPending,
        isViewPending: viewMutation.isPending,
        refresh: () => {
            refetchSummary();
            refetchTrend();
        },
        startSync: () => syncMutation.mutate(),
        scrapePlace: (keyword: string) => placeMutation.mutate(keyword),
        scrapeView: (keyword: string) => viewMutation.mutate(keyword)
    };
}
