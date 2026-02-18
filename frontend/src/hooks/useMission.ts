import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { scrapePlace, scrapeView, analyzeSOV, getRankings, getCompetitors } from '@/lib/api';
import { ScrapeResponse } from '@/types/mission';
import { useClient } from '@/components/providers/ClientProvider';

export function useMission() {
    const { selectedClient } = useClient();
    const [keyword, setKeyword] = useState('');
    const [targetHospital, setTargetHospital] = useState('');
    const [topN, setTopN] = useState(10);

    // Initialize state when selectedClient changes
    useEffect(() => {
        if (selectedClient) {
            // Default to client name or industry if keyword is empty?
            // Usually keyword is specific, but targetHospital is likely the client name.
            if (!targetHospital) setTargetHospital(selectedClient.name);
            // We can't easily guess keyword, but maybe '업종 + 지역'?
            // For now, leave keyword empty to force user input or load from saved preferences if we had them.
        }
    }, [selectedClient, targetHospital]);

    // Scraping Mutations
    const placeMutation = useMutation({
        mutationFn: (keyword: string) => scrapePlace(keyword, selectedClient?.id),
        onError: (error) => {
            console.error("Place Scrape Error:", error);
        }
    });

    const viewMutation = useMutation({
        mutationFn: (keyword: string) => scrapeView(keyword, selectedClient?.id),
        onError: (error) => {
            console.error("View Scrape Error:", error);
        }
    });

    // Data Queries - Only run if keyword and targetHospital are set
    const isEnabled = !!keyword && !!targetHospital;

    const { data: sovData, refetch: refetchSOV, isError: isSovError } = useQuery({
        queryKey: ['sov', keyword, targetHospital, topN],
        queryFn: () => analyzeSOV({ target_hospital: targetHospital, keywords: [keyword], top_n: topN }),
        enabled: isEnabled,
        retry: 1, // Don't retry endlessly
    });

    const { data: placeRankings, refetch: refetchPlaceRanks, isError: isPlaceError } = useQuery({
        queryKey: ['rankings', 'place', keyword],
        queryFn: () => getRankings(keyword, 'NAVER_PLACE'),
        enabled: !!keyword,
        retry: 1,
    });

    const { data: viewRankings, refetch: refetchViewRanks, isError: isViewError } = useQuery({
        queryKey: ['rankings', 'view', keyword],
        queryFn: () => getRankings(keyword, 'NAVER_VIEW'),
        enabled: !!keyword,
        retry: 1,
    });

    const { data: placeCompetitors, refetch: refetchPlaceComp, isError: isPlaceCompError } = useQuery({
        queryKey: ['competitors', 'place', keyword, topN],
        queryFn: () => getCompetitors(keyword, 'NAVER_PLACE', topN),
        enabled: !!keyword,
        retry: 1,
    });

    const { data: viewCompetitors, refetch: refetchViewComp, isError: isViewCompError } = useQuery({
        queryKey: ['competitors', 'view', keyword, topN],
        queryFn: () => getCompetitors(keyword, 'NAVER_VIEW', topN),
        enabled: !!keyword,
        retry: 1,
    });

    const handleRefresh = () => {
        if (!isEnabled) return;
        refetchSOV();
        refetchPlaceRanks();
        refetchViewRanks();
        refetchPlaceComp();
        refetchViewComp();
    };

    return {
        keyword, setKeyword,
        targetHospital, setTargetHospital,
        topN, setTopN,
        placeMutation,
        viewMutation,
        sovData,
        placeRankings,
        viewRankings,
        placeCompetitors,
        viewCompetitors,
        handleRefresh,
        errors: {
            sov: isSovError,
            place: isPlaceError,
            view: isViewError,
            placeComp: isPlaceCompError,
            viewComp: isViewCompError
        }
    };
}
