import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    UserPlus,
    Target,
    Search,
    ChevronRight,
    ChevronLeft,
    Plus,
    Trash2,
    CheckCircle2,
    Sparkles,
    ArrowRight,
    Building2,
    Link as LinkIcon,
    History,
    RefreshCw,
    Briefcase,
    X,
    AlertCircle
} from 'lucide-react';
import clsx from 'clsx';
import { createClient, updateBulkTargets, searchClients, searchTargets, saveAnalysisHistory, getAnalysisHistory, getClients, scrapePlace, scrapeView, scrapeAd, getScrapeResults } from '@/lib/api'; // [FIX Bug#9] scrapeAd 추가
import { toast } from 'sonner';
import { useClient } from '@/components/providers/ClientProvider';
import { useAuth } from '@/components/providers/AuthProvider';
import { ScrapeResultsDisplay } from './ScrapeResultsDisplay';
import { TargetItem, Client } from '@/types';

type Step = 1 | 2 | 3;

interface SetupWizardProps {
    onComplete?: () => void;
}

export function SetupWizard({ onComplete }: SetupWizardProps) {
    const router = useRouter();
    const { refreshClients, selectedClient, setSelectedClient } = useClient();
    const [currentStep, setCurrentStep] = useState<Step>(selectedClient ? 3 : 1);
    const { user } = useAuth();

    // Step 1 State: Client Info
    const [clientName, setClientName] = useState('');
    const [industry, setIndustry] = useState('이커머스');
    const [newClientId, setNewClientId] = useState<string | null>(null);
    const [clientSuggestions, setClientSuggestions] = useState<Client[]>([]);
    const [recentClients, setRecentClients] = useState<Client[]>([]);

    // Step 2 State: Targets
    const [targets, setTargets] = useState<TargetItem[]>([
        { name: '', target_type: 'OWNER', url: '' }
    ]);
    const [targetSuggestions, setTargetSuggestions] = useState<any[]>([]);
    const [recentTargets, setRecentTargets] = useState<any[]>([]);
    const [activeTargetIdx, setActiveTargetIdx] = useState<number | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Step 3 State: Analysis Setup
    const [keyword, setKeyword] = useState('');
    const [platform, setPlatform] = useState('NAVER_PLACE');
    const [history, setHistory] = useState<any[]>([]);
    const [scrapeResults, setScrapeResults] = useState<any>(null);
    const [showResults, setShowResults] = useState(false);
    // [NEW] Error tracking for scraping operations
    const [scrapeError, setScrapeError] = useState<string | null>(null);
    const [scrapingStatus, setScrapingStatus] = useState<'idle' | 'scraping' | 'fetching' | 'done' | 'error'>('idle');

    // Initial Data Load
    useEffect(() => {
        getClients().then(setRecentClients);
        searchTargets('').then(setRecentTargets);

        // Load analysis history if client is selected
        if (selectedClient) {
            console.log(`📊 Loading analysis history for client: ${selectedClient.id}`);
            getAnalysisHistory(selectedClient.id)
                .then((data) => {
                    console.log(`✅ Analysis history loaded:`, data);
                    setHistory(data);
                })
                .catch((err) => {
                    console.error(`❌ Failed to load analysis history:`, err);
                    setHistory([]);
                });
        }
    }, [selectedClient]);

    // Client Search Effect
    useEffect(() => {
        if (clientName.length > 1) {
            const delayDebounceFn = setTimeout(async () => {
                const results = await searchClients(clientName);
                setClientSuggestions(results);
            }, 300);
            return () => clearTimeout(delayDebounceFn);
        } else {
            setClientSuggestions([]);
        }
    }, [clientName]);

    // Target Search Effect
    const activeTargetName = activeTargetIdx !== null ? targets[activeTargetIdx]?.name : undefined;

    useEffect(() => {
        if (activeTargetIdx !== null) {
            const query = targets[activeTargetIdx]?.name || '';

            // If empty query, fetch immediately for snappy "quick select" experience
            if (!query) {
                searchTargets('').then(setTargetSuggestions);
                return;
            }

            const delayDebounceFn = setTimeout(async () => {
                const results = await searchTargets(query);
                setTargetSuggestions(results);
            }, 300);
            return () => clearTimeout(delayDebounceFn);
        } else {
            setTargetSuggestions([]);
        }
    }, [activeTargetIdx, activeTargetName]);

    // History Effect
    useEffect(() => {
        if (newClientId) {
            getAnalysisHistory(newClientId).then(setHistory);
        } else if (selectedClient) {
            setNewClientId(selectedClient.id);
            setClientName(selectedClient.name);
            setIndustry(selectedClient.industry || '이커머스');
            getAnalysisHistory(selectedClient.id).then(h => {
                setHistory(h);
                if (h.length > 0) {
                    setKeyword(h[0].keyword);
                    setPlatform(h[0].platform);
                }
            });
        }
    }, [newClientId, selectedClient]);

    const handleSelectExistingClient = (client: Client) => {
        setClientName(client.name);
        setIndustry(client.industry || '이커머스');
        setNewClientId(client.id);
        setSelectedClient(client);

        // Sync to targets
        setTargets(prev => {
            const newTargets = [...prev];
            if (newTargets.length > 0 && newTargets[0].target_type === 'OWNER' && !newTargets[0].name) {
                newTargets[0].name = client.name;
            }
            return newTargets;
        });

        setCurrentStep(2);
    };

    const handleSelectExistingTarget = (target: any) => {
        // Find the first row that doesn't have a name yet (including OWNER)
        const emptyIdx = targets.findIndex(t => !t.name);
        if (emptyIdx !== -1) {
            updateTarget(emptyIdx, 'name', target.name);
            updateTarget(emptyIdx, 'url', target.url || target.urls?.default || '');
        } else {
            setTargets([...targets, { name: target.name, target_type: 'COMPETITOR', url: target.url || target.urls?.default || '' }]);
        }
    };

    const handleNext = async () => {
        if (currentStep === 1) {
            if (!clientName) { toast.error('브랜드명을 입력해주세요.'); return; }
            try {
                const existing = clientSuggestions.find(c => c.name === clientName) || recentClients.find(c => c.name === clientName);
                if (existing) {
                    setNewClientId(existing.id);
                    setSelectedClient(existing);
                } else {
                    const created = await createClient({
                        name: clientName,
                        industry,
                        agency_id: user?.agency_id || '00000000-0000-0000-0000-000000000000'
                    });
                    setNewClientId(created.id);
                    setSelectedClient(created);
                    await refreshClients();
                }

                // Sync client name to the first target (OWNER) if it's empty
                setTargets(prev => {
                    const newTargets = [...prev];
                    if (newTargets.length > 0 && newTargets[0].target_type === 'OWNER' && !newTargets[0].name) {
                        newTargets[0].name = clientName;
                    }
                    return newTargets;
                });

                setCurrentStep(2);
            } catch {
                toast.error('브랜드 등록 중 오류가 발생했습니다.');
            }
        } else if (currentStep === 2) {
            // Filter out targets with completely empty names
            const validTargets = targets.filter(t => t.name.trim() !== '');

            if (validTargets.length === 0) {
                toast.error('최소 한 개의 분석 대상을 입력해주세요.'); return;
            }

            try {
                await updateBulkTargets({
                    client_id: newClientId!,
                    targets: validTargets
                });
                setCurrentStep(3);
            } catch {
                toast.error('타겟 등록 중 오류가 발생했습니다.');
            }
        } else {
            if (!keyword) { toast.error('조사 키워드를 입력해주세요.'); return; }
            if (isSubmitting) {
                toast.info('이미 조사가 진행 중입니다. 잠시만 기다려주세요.');
                return;
            }
            // Prevent concurrent scraping requests for the same setup
            if (scrapingStatus === 'scraping' || scrapingStatus === 'fetching') {
                toast.warning('조사가 진행 중입니다. 완료될 때까지 기다려주세요.');
                return;
            }

            setIsSubmitting(true);
            try {
                // Step 1: Save analysis history
                console.log(`🚀 Starting analysis: keyword="${keyword}", platform="${platform}", clientId="${newClientId}"`);

                const historyResponse = await saveAnalysisHistory({
                    client_id: newClientId!,
                    keyword,
                    platform
                });
                console.log('✅ [Step 1] Analysis history saved:', historyResponse);
                console.log('   Response type:', typeof historyResponse, 'Keys:', Object.keys(historyResponse || {}));

                // Step 2: Trigger scraping and fetch results
                console.log(`🔄 [Step 2] Triggering scraping for platform: ${platform}`);
                toast.info('조사를 시작했습니다. 결과를 수집 중입니다...');

                // [UPDATED] Error tracking added
                setScrapingStatus('scraping');
                setScrapeError(null);
                
                if (platform === 'NAVER_PLACE') {
                    scrapePlace(keyword, newClientId!)
                        .then((data) => {
                            console.log('✅ [Step 2-A] Place scraping triggered');
                            console.log('   Response:', data);
                        })
                        .catch((err) => {
                            console.error('⚠️ [Step 2-A] Place scraping failed:', {
                                status: err?.response?.status,
                                message: err?.message,
                                detail: err?.response?.data?.detail
                            });
                            // [NEW] Set error state
                            const errorMsg = err?.response?.data?.detail || err?.message || '스크래핑 중 알 수 없는 오류 발생';
                            setScrapeError(errorMsg);
                            setScrapingStatus('error');
                            toast.error(`스크래핑 실패: ${errorMsg}`);
                        });
                } else if (platform === 'NAVER_VIEW') {
                    scrapeView(keyword, newClientId!)
                        .then((data) => {
                            console.log('✅ [Step 2-B] View scraping triggered');
                            console.log('   Response:', data);
                        })
                        .catch((err) => {
                            console.error('⚠️ [Step 2-B] View scraping failed:', {
                                status: err?.response?.status,
                                message: err?.message,
                                detail: err?.response?.data?.detail
                            });
                            const errorMsg = err?.response?.data?.detail || err?.message || '스크래핑 중 알 수 없는 오류 발생';
                            setScrapeError(errorMsg);
                            setScrapingStatus('error');
                            toast.error(`스크래핑 실패: ${errorMsg}`);
                        });
                } else if (platform === 'NAVER_AD') {
                    // [FIX Bug#8] NAVER_AD 스크래핑 추가
                    scrapeAd(keyword, newClientId!)
                        .then((data) => {
                            console.log('✅ [Step 2-C] Ad scraping triggered');
                            console.log('   Response:', data);
                        })
                        .catch((err) => {
                            console.error('⚠️ [Step 2-C] Ad scraping failed:', {
                                status: err?.response?.status,
                                message: err?.message,
                                detail: err?.response?.data?.detail
                            });
                            const errorMsg = err?.response?.data?.detail || err?.message || '스크래핑 중 알 수 없는 오류 발생';
                            setScrapeError(errorMsg);
                            setScrapingStatus('error');
                            toast.error(`스크래핑 실패: ${errorMsg}`);
                        });
                }

                // Step 3: Polling for scraping results (dynamic wait time)
                console.log(`⏳ [Step 3] Starting to fetch scrape results with polling...`);
                setScrapingStatus('fetching');

                // Polling function with exponential backoff
                const pollForResults = async () => {
                    const maxWaitTime = 90000; // [FIX Bug#10] 30s → 90s (스크래핑 완료 시간 고려)
                    const initialPollInterval = 500; // Start with 500ms
                    const maxPollInterval = 3000; // Max 3 seconds between polls
                    let pollInterval = initialPollInterval;
                    let totalWaitTime = 0;
                    let pollAttempts = 0;

                    const poll = async (): Promise<boolean> => {
                        pollAttempts++;
                        try {
                            console.log(`🔍 [Step 3-A] Poll attempt #${pollAttempts}, waited ${totalWaitTime}ms`);
                            const results = await getScrapeResults(newClientId!, keyword, platform);
                            console.log('📊 Scrape results:', results);

                            if (results.has_data && results.results.length > 0) {
                                console.log(`✅ [Step 3-B] Found ${results.results.length} results after ${pollAttempts} attempts`);
                                setScrapeResults(results);
                                setShowResults(true);
                                setScrapingStatus('done');
                                toast.success('조사가 완료되었습니다! 결과를 확인하세요.');
                                return true;
                            } else {
                                console.log(`⚠️ [Step 3-B] No data yet, will retry...`);

                                // If we have partial data (keyword exists but no results yet), keep polling
                                if (results.keyword === keyword && totalWaitTime < maxWaitTime) {
                                    // Increase poll interval exponentially
                                    pollInterval = Math.min(pollInterval * 1.5, maxPollInterval);

                                    // Schedule next poll
                                    await new Promise(resolve => setTimeout(resolve, pollInterval));
                                    totalWaitTime += pollInterval;

                                    return await poll();
                                } else {
                                    // Timeout reached or no keyword record
                                    console.log(`⏱️ [Step 3-C] Polling timeout or no keyword record`);
                                    setScrapeResults(results);
                                    setShowResults(true);
                                    setScrapingStatus('done');
                                    toast.info('조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다.');
                                    return true;
                                }
                            }
                        } catch (err) {
                            console.error(`❌ Poll attempt #${pollAttempts} failed:`, err);

                            if (totalWaitTime < maxWaitTime) {
                                pollInterval = Math.min(pollInterval * 1.5, maxPollInterval);
                                await new Promise(resolve => setTimeout(resolve, pollInterval));
                                totalWaitTime += pollInterval;
                                return await poll();
                            } else {
                                throw err;
                            }
                        }
                    };

                    try {
                        await poll();
                    } catch (err) {
                        console.error('❌ Polling failed after all attempts:', err);
                        const errorMsg = (err as any)?.response?.data?.detail || (err as any)?.message || '결과 수집 중 오류 발생';
                        setScrapeError(errorMsg);
                        setScrapingStatus('error');
                        toast.error(`결과 조회 실패: ${errorMsg}`);
                        setShowResults(false);
                    } finally {
                        setIsSubmitting(false);
                    }
                };

                // Start polling asynchronously
                pollForResults();
            } catch (error: any) {
                console.error('❌ Analysis setup error:', error);

                // Extract error message from various sources
                const errorMessage =
                    error?.response?.data?.detail ||
                    error?.message ||
                    '분석 이력 저장 중 오류가 발생했습니다.';

                setScrapeError(errorMessage);
                setScrapingStatus('error');
                toast.error(`오류: ${errorMessage}`);
                setIsSubmitting(false);
            }
        }
    };

    const addTarget = () => {
        setTargets([...targets, { name: '', target_type: 'COMPETITOR', url: '' }]);
    };

    const removeTarget = (index: number) => {
        setTargets(targets.filter((_, i) => i !== index));
    };

    const updateTarget = (index: number, field: keyof TargetItem, value: any) => {
        const newTargets = [...targets];
        newTargets[index] = { ...newTargets[index], [field]: value };
        setTargets(newTargets);
    };

    const selectHistory = (h: any) => {
        setKeyword(h.keyword);
        setPlatform(h.platform);
    };

    return (
        <div className="">
            {/* Step Indicator */}
            <div className="mb-8">
                <div className="flex items-center justify-between max-w-md mx-auto relative">
                    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-secondary -translate-y-1/2 z-0" />
                    <div className={clsx("absolute top-1/2 left-0 h-0.5 bg-primary transition-all duration-500 -translate-y-1/2 z-0",
                        currentStep === 1 ? "w-0" : currentStep === 2 ? "w-1/2" : "w-full")} />

                    {[
                        { step: 1, icon: UserPlus, label: '브랜드' },
                        { step: 2, icon: Target, label: '타켓' },
                        { step: 3, icon: Search, label: '조사' }
                    ].map((s) => (
                        <div key={s.step} className="relative z-10 flex flex-col items-center gap-2">
                            <div className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                                currentStep >= s.step ? "bg-primary border-primary text-white shadow-lg shadow-primary/20" : "bg-card border-border text-muted-foreground"
                            )}>
                                <s.icon className="w-4 h-4" />
                            </div>
                            <span className={clsx("text-[10px] font-bold", currentStep >= s.step ? "text-primary" : "text-muted-foreground")}>
                                {s.label}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div className="bg-card/70 backdrop-blur-xl border border-white/40 rounded-3xl p-6 sm:p-8 shadow-xl shadow-foreground/10 flex flex-col relative overflow-visible">
                <div className="flex-1">
                    {currentStep === 1 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div>
                                <h2 className="text-3xl font-bold text-foreground mb-2">어떤 브랜드를 분석할까요?</h2>
                                <p className="text-muted-foreground">기존 브랜드를 선택하거나 새 브랜드를 등록해주세요.</p>
                            </div>

                            {recentClients.length > 0 && (
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-foreground flex items-center gap-2">
                                        <Briefcase className="w-4 h-4 text-primary" /> 등록된 브랜드 (퀵 셀렉트)
                                    </label>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                        {recentClients.slice(0, 6).map(client => (
                                            <button
                                                key={client.id}
                                                onClick={() => handleSelectExistingClient(client)}
                                                className="group p-4 bg-card border border-border rounded-2xl text-left hover:border-primary hover:shadow-lg hover:shadow-primary/5 transition-all outline-none"
                                            >
                                                <div className="text-xs text-muted-foreground mb-1 group-hover:text-primary transition-colors">{client.industry}</div>
                                                <div className="font-bold text-foreground line-clamp-1">{client.name}</div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-6 max-w-md relative pt-6 border-t border-border">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-foreground flex items-center gap-2">
                                        <Plus className="w-4 h-4 text-primary" /> 새 브랜드 등록
                                    </label>
                                    <input
                                        type="text"
                                        value={clientName}
                                        onChange={(e) => setClientName(e.target.value)}
                                        placeholder="브랜드명을 입력하세요"
                                        className="w-full h-14 bg-background/50 border border-border rounded-2xl px-5 text-lg focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all outline-none"
                                    />
                                    {clientSuggestions.length > 0 && (
                                        <div className="absolute top-[85px] left-0 w-full bg-card border border-border rounded-2xl shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                            {clientSuggestions.map(c => (
                                                <button
                                                    key={c.id}
                                                    onClick={() => handleSelectExistingClient(c)}
                                                    className="w-full px-5 py-4 text-left hover:bg-secondary flex items-center justify-between group transition-colors"
                                                >
                                                    <div>
                                                        <span className="font-bold text-foreground">{c.name}</span>
                                                        <span className="ml-2 text-xs text-muted-foreground">{c.industry}</span>
                                                    </div>
                                                    <ChevronRight className="w-4 h-4 text-muted-foreground/60 group-hover:text-primary transition-colors" />
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-foreground">카테고리</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {['이커머스', '뷰티', '식음료', '기타'].map(opt => (
                                            <button
                                                key={opt}
                                                onClick={() => setIndustry(opt)}
                                                className={clsx(
                                                    "h-12 rounded-xl text-sm font-bold transition-all border",
                                                    industry === opt ? "bg-primary/10 border-primary text-primary" : "bg-card border-border text-muted-foreground hover:border-border"
                                                )}
                                            >
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {currentStep === 2 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div>
                                <h2 className="text-3xl font-bold text-foreground mb-2">분석 대상을 지정해주세요</h2>
                                <p className="text-muted-foreground">우리 브랜드와 비교하고 싶은 경쟁 브랜드를 등록합니다.</p>
                            </div>

                            {recentTargets.length > 0 && (
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-foreground flex items-center gap-2">
                                        <Sparkles className="w-4 h-4 text-primary" /> 추천/최근 브랜드 (퀵 셀렉트)
                                    </label>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                        {recentTargets.slice(0, 8).map(s => (
                                            <button
                                                key={s.id}
                                                onClick={() => handleSelectExistingTarget(s)}
                                                className="p-3 bg-card border border-border rounded-xl text-xs font-bold text-muted-foreground hover:border-primary hover:bg-primary/5 hover:text-primary transition-all shadow-sm flex flex-col gap-1 text-left"
                                            >
                                                <div className="flex items-center gap-1">
                                                    <Plus className="w-3 h-3 text-primary" />
                                                    <span className="line-clamp-1">{s.name}</span>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-4 pt-6 border-t border-border">
                                {targets.map((t, idx) => (
                                    <div key={idx} className={clsx(
                                        "p-6 rounded-2xl border transition-all flex items-center gap-4 relative overflow-visible",
                                        t.target_type === 'OWNER' ? "bg-primary/10 border-primary ring-2 ring-primary/10" : "bg-card border-border shadow-sm"
                                    )}>
                                        <div className={clsx(
                                            "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0",
                                            t.target_type === 'OWNER' ? "bg-primary text-white" : "bg-secondary text-muted-foreground"
                                        )}>
                                            {t.target_type === 'OWNER' ? '나' : idx}
                                        </div>
                                        <div className="flex-1 grid grid-cols-2 gap-4">
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    placeholder="브랜드 이름"
                                                    value={t.name}
                                                    onFocus={() => setActiveTargetIdx(idx)}
                                                    onBlur={() => setTimeout(() => setActiveTargetIdx(null), 200)}
                                                    onChange={(e) => updateTarget(idx, 'name', e.target.value)}
                                                    className="w-full bg-transparent border-b border-input py-2 outline-none focus:border-primary font-bold transition-all"
                                                />
                                                {activeTargetIdx === idx && targetSuggestions.length > 0 && (
                                                    <div className="absolute top-[45px] left-0 w-full bg-card border border-border rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                        {targetSuggestions.map(s => (
                                                            <button
                                                                key={s.id}
                                                                onClick={() => {
                                                                    updateTarget(idx, 'name', s.name);
                                                                    updateTarget(idx, 'url', s.urls?.default || '');
                                                                    setTargetSuggestions([]);
                                                                }}
                                                                className="w-full px-4 py-3 text-left hover:bg-secondary flex items-center justify-between group transition-colors text-sm"
                                                            >
                                                                <span className="font-bold text-foreground">{s.name}</span>
                                                                <LinkIcon className="w-3 h-3 text-muted-foreground/60" />
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <LinkIcon className="w-4 h-4 text-muted-foreground" />
                                                <input
                                                    type="url"
                                                    placeholder="네이버 플레이스 URL (선택)"
                                                    value={t.url}
                                                    onChange={(e) => updateTarget(idx, 'url', e.target.value)}
                                                    className="flex-1 bg-transparent border-b border-border py-2 outline-none focus:border-primary text-sm transition-all text-muted-foreground"
                                                />
                                            </div>
                                        </div>
                                        {t.target_type === 'COMPETITOR' && (
                                            <button onClick={() => removeTarget(idx)} className="text-muted-foreground/60 hover:text-red-500 transition-colors">
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        )}
                                    </div>
                                ))}
                                <button
                                    onClick={addTarget}
                                    className="w-full h-14 border-2 border-dashed border-input rounded-2xl flex items-center justify-center gap-2 text-muted-foreground hover:border-primary hover:text-primary transition-all font-bold"
                                >
                                    <Plus className="w-5 h-5" /> 경쟁사 추가하기
                                </button>
                            </div>
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div>
                                <h2 className="text-3xl font-bold text-foreground mb-2">어떤 검색어로 조사할까요?</h2>
                                <p className="text-muted-foreground">마지막입니다! 분석하고 싶은 키워드와 매체를 선택하세요.</p>
                            </div>

                            <div className="space-y-10">
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-foreground">조사 키워드</label>
                                    <div className="relative max-w-md">
                                        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-muted-foreground w-5 h-5" />
                                        <input
                                            type="text"
                                            placeholder="예: 제주도여행"
                                            value={keyword}
                                            onChange={(e) => setKeyword(e.target.value)}
                                            disabled={scrapingStatus === 'scraping' || scrapingStatus === 'fetching'}
                                            className="w-full h-16 bg-background/50 border border-border rounded-2xl pl-12 pr-5 text-xl font-bold focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all outline-none shadow-sm disabled:opacity-50"
                                        />
                                    </div>
                                    {scrapeError && scrapingStatus === 'error' && (
                                        <div className="mt-3 p-4 bg-red-50 border border-red-200 rounded-xl">
                                            <p className="text-sm font-semibold text-red-700">⚠️ 조사 실패</p>
                                            <p className="text-sm text-red-600 mt-1">{scrapeError}</p>
                                            <button
                                                onClick={() => {
                                                    setScrapeError(null);
                                                    setScrapingStatus('idle');
                                                }}
                                                className="text-xs font-bold text-red-700 mt-2 hover:underline"
                                            >
                                                다시 시도하기
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-foreground">분석 매체</label>
                                    <div className="flex gap-4">
                                        {[
                                            { id: 'NAVER_PLACE', name: '네이버 플레이스', color: 'bg-green-500' },
                                            { id: 'NAVER_VIEW', name: '네이버 VIEW(블로그)', color: 'bg-emerald-500' },
                                            { id: 'NAVER_AD', name: '네이버 파워링크(광고)', color: 'bg-blue-500' } // [FIX Bug#8]
                                        ].map(p => (
                                            <button
                                                key={p.id}
                                                onClick={() => setPlatform(p.id)}
                                                className={clsx(
                                                    "px-6 py-4 rounded-2xl font-bold transition-all border flex items-center gap-3",
                                                    platform === p.id ? "bg-card border-primary text-primary shadow-lg shadow-primary/5" : "bg-background border-border text-muted-foreground"
                                                )}
                                            >
                                                <div className={clsx("w-2 h-2 rounded-full", p.color)} />
                                                {p.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {history.length > 0 && (
                                    <div className="space-y-4 pt-6 border-t border-border">
                                        <label className="text-sm font-bold text-foreground flex items-center gap-2">
                                            <History className="w-4 h-4 text-primary" /> 최근 분석 이력
                                        </label>
                                        <div className="flex flex-wrap gap-2">
                                            {history.map((h, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => selectHistory(h)}
                                                    className="px-4 py-2 bg-background border border-border rounded-full text-xs font-bold text-muted-foreground hover:bg-primary hover:text-white hover:border-primary transition-all flex items-center gap-2 group"
                                                >
                                                    {h.keyword}
                                                    <span className="text-[10px] opacity-40 group-hover:opacity-100">{h.platform.split('_')[1]}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Scraping Results Display */}
                {showResults && scrapeResults && currentStep === 3 && (
                    <ScrapeResultsDisplay
                        scrapeResults={scrapeResults}
                        onContinue={() => {
                            setShowResults(false);
                            setIsSubmitting(false);
                            toast.success('대시보드로 이동합니다...');
                            setTimeout(() => {
                                if (onComplete) {
                                    onComplete();
                                } else {
                                    router.push('/dashboard');
                                }
                            }, 500);
                        }}
                        onRetry={() => {
                            setShowResults(false);
                            setIsSubmitting(false);
                        }}
                    />
                )}

                {/* Footer Buttons */}
                <div className="mt-12 flex items-center justify-between pt-8 border-t border-border">
                    <button
                        disabled={currentStep === 1}
                        onClick={() => setCurrentStep(prev => prev > 1 ? (prev - 1) as Step : prev)}
                        className="flex items-center gap-2 text-muted-foreground font-bold hover:text-foreground transition-colors disabled:opacity-0"
                    >
                        <ChevronLeft className="w-5 h-5" /> 이전으로
                    </button>
                    <button
                        onClick={handleNext}
                        disabled={isSubmitting}
                        className={clsx(
                            "h-16 px-10 bg-primary text-white font-bold rounded-2xl shadow-xl shadow-primary/30 hover:shadow-primary/40 active:scale-95 transition-all flex items-center gap-3 text-lg",
                            isSubmitting && "opacity-70 cursor-not-allowed"
                        )}
                    >
                        {isSubmitting ? (
                            <>처리 중...</>
                        ) : (
                            <>
                                {currentStep === 3 ? "조사 시작" : "다음 단계로"}
                                {currentStep === 3 ? <RefreshCw className="w-6 h-6" /> : <ChevronRight className="w-5 h-5" />}
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
