import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { scrapePlace, scrapeView, getSOV, getRankings, getCompetitors } from '@/lib/api';
import { ScrapeResponse } from '@/types/mission';

export function useMission() {
    const [keyword, setKeyword] = useState('송도 치과');
    const [targetHospital, setTargetHospital] = useState('기록하는 습관');
    const [topN, setTopN] = useState(10);

    // Scraping Mutations
    const placeMutation = useMutation({
        mutationFn: scrapePlace,
    });

    const viewMutation = useMutation({
        mutationFn: scrapeView,
    });

    // Data Queries
    const { data: sovData, refetch: refetchSOV } = useQuery({
        queryKey: ['sov', keyword, targetHospital, topN],
        queryFn: () => getSOV(targetHospital, [keyword], topN),
        enabled: !!keyword && !!targetHospital,
    });

    const { data: placeRankings, refetch: refetchPlaceRanks } = useQuery({
        queryKey: ['rankings', 'place', keyword],
        queryFn: () => getRankings(keyword, 'NAVER_PLACE'),
        enabled: !!keyword,
    });

    const { data: viewRankings, refetch: refetchViewRanks } = useQuery({
        queryKey: ['rankings', 'view', keyword],
        queryFn: () => getRankings(keyword, 'NAVER_VIEW'),
        enabled: !!keyword,
    });

    const { data: placeCompetitors, refetch: refetchPlaceComp } = useQuery({
        queryKey: ['competitors', 'place', keyword, topN],
        queryFn: () => getCompetitors(keyword, 'NAVER_PLACE', topN),
        enabled: !!keyword,
    });

    const { data: viewCompetitors, refetch: refetchViewComp } = useQuery({
        queryKey: ['competitors', 'view', keyword, topN],
        queryFn: () => getCompetitors(keyword, 'NAVER_VIEW', topN),
        enabled: !!keyword,
    });

    const handleRefresh = () => {
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
        handleRefresh
    };
}
