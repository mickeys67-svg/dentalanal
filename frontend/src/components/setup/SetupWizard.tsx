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
    X
} from 'lucide-react';
import clsx from 'clsx';
import { createClient, updateBulkTargets, searchClients, searchTargets, saveAnalysisHistory, getAnalysisHistory, getClients, scrapePlace, scrapeView } from '@/lib/api';
import { useClient } from '@/components/providers/ClientProvider';
import { useAuth } from '@/components/providers/AuthProvider';
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
    const [industry, setIndustry] = useState('치과의원');
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

    // Initial Data Load
    useEffect(() => {
        getClients().then(setRecentClients);
        searchTargets('').then(setRecentTargets);
    }, []);

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
    }, [activeTargetIdx, activeTargetIdx !== null ? targets[activeTargetIdx]?.name : undefined]);

    // History Effect
    useEffect(() => {
        if (newClientId) {
            getAnalysisHistory(newClientId).then(setHistory);
        } else if (selectedClient) {
            setNewClientId(selectedClient.id);
            setClientName(selectedClient.name);
            setIndustry(selectedClient.industry || '치과의원');
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
        setIndustry(client.industry || '치과의원');
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
            if (!clientName) return alert('업체명을 입력해주세요.');
            try {
                const existing = clientSuggestions.find(c => c.name === clientName) || recentClients.find(c => c.name === clientName);
                let clientId = newClientId;
                let client = selectedClient;

                if (existing) {
                    clientId = existing.id;
                    setNewClientId(existing.id);
                    setSelectedClient(existing);
                    client = existing;
                } else {
                    const created = await createClient({
                        name: clientName,
                        industry,
                        agency_id: user?.agency_id || '00000000-0000-0000-0000-000000000000'
                    });
                    clientId = created.id;
                    setNewClientId(created.id);
                    setSelectedClient(created);
                    client = created;
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
            } catch (error) {
                alert('업체 등록 중 오류가 발생했습니다.');
            }
        } else if (currentStep === 2) {
            // Filter out targets with completely empty names
            const validTargets = targets.filter(t => t.name.trim() !== '');

            if (validTargets.length === 0) {
                return alert('최소 한 개의 분석 대상을 입력해주세요.');
            }

            try {
                await updateBulkTargets({
                    client_id: newClientId!,
                    targets: validTargets
                });
                setCurrentStep(3);
            } catch (error) {
                alert('타겟 등록 중 오류가 발생했습니다.');
            }
        } else {
            if (!keyword) return alert('조사 키워드를 입력해주세요.');
            if (isSubmitting) return;

            setIsSubmitting(true);
            try {
                await saveAnalysisHistory({
                    client_id: newClientId!,
                    keyword,
                    platform
                });

                // Trigger immediate scraping - Don't await here to prevent navigation block
                if (platform === 'NAVER_PLACE') {
                    scrapePlace(keyword, newClientId!).catch(console.error);
                } else if (platform === 'NAVER_VIEW') {
                    scrapeView(keyword, newClientId!).catch(console.error);
                }

                // Small delay to ensure state/history is updated on backend
                setTimeout(() => {
                    if (onComplete) {
                        onComplete();
                    } else {
                        router.push('/dashboard');
                    }
                }, 100);
            } catch (error) {
                console.error("Analysis save error:", error);
                alert('분석 이력 저장 중 오류가 발생했습니다.');
            } finally {
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
                    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-100 -translate-y-1/2 z-0" />
                    <div className={clsx("absolute top-1/2 left-0 h-0.5 bg-primary transition-all duration-500 -translate-y-1/2 z-0",
                        currentStep === 1 ? "w-0" : currentStep === 2 ? "w-1/2" : "w-full")} />

                    {[
                        { step: 1, icon: UserPlus, label: '광고주' },
                        { step: 2, icon: Target, label: '타켓' },
                        { step: 3, icon: Search, label: '조사' }
                    ].map((s) => (
                        <div key={s.step} className="relative z-10 flex flex-col items-center gap-2">
                            <div className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                                currentStep >= s.step ? "bg-primary border-primary text-white shadow-lg shadow-primary/20" : "bg-white border-gray-200 text-gray-400"
                            )}>
                                <s.icon className="w-4 h-4" />
                            </div>
                            <span className={clsx("text-[10px] font-bold", currentStep >= s.step ? "text-primary" : "text-gray-400")}>
                                {s.label}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div className="bg-white/70 backdrop-blur-xl border border-white/40 rounded-3xl p-6 sm:p-8 shadow-xl shadow-gray-200/50 flex flex-col relative overflow-visible">
                <div className="flex-1">
                    {currentStep === 1 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div>
                                <h2 className="text-3xl font-bold text-gray-900 mb-2">누구를 위한 분석인가요?</h2>
                                <p className="text-gray-500">기존 업체를 선택하거나 새 업체를 등록해주세요.</p>
                            </div>

                            {recentClients.length > 0 && (
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <Briefcase className="w-4 h-4 text-primary" /> 등록된 업체 (퀵 셀렉트)
                                    </label>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                        {recentClients.slice(0, 6).map(client => (
                                            <button
                                                key={client.id}
                                                onClick={() => handleSelectExistingClient(client)}
                                                className="group p-4 bg-white border border-gray-100 rounded-2xl text-left hover:border-primary hover:shadow-lg hover:shadow-primary/5 transition-all outline-none"
                                            >
                                                <div className="text-xs text-gray-400 mb-1 group-hover:text-primary transition-colors">{client.industry}</div>
                                                <div className="font-bold text-gray-800 line-clamp-1">{client.name}</div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-6 max-w-md relative pt-6 border-t border-gray-50">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <Plus className="w-4 h-4 text-primary" /> 새 업체 등록
                                    </label>
                                    <input
                                        type="text"
                                        value={clientName}
                                        onChange={(e) => setClientName(e.target.value)}
                                        placeholder="업체명을 입력하세요"
                                        className="w-full h-14 bg-gray-50/50 border border-gray-100 rounded-2xl px-5 text-lg focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all outline-none"
                                    />
                                    {clientSuggestions.length > 0 && (
                                        <div className="absolute top-[85px] left-0 w-full bg-white border border-gray-100 rounded-2xl shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                            {clientSuggestions.map(c => (
                                                <button
                                                    key={c.id}
                                                    onClick={() => handleSelectExistingClient(c)}
                                                    className="w-full px-5 py-4 text-left hover:bg-gray-50 flex items-center justify-between group transition-colors"
                                                >
                                                    <div>
                                                        <span className="font-bold text-gray-800">{c.name}</span>
                                                        <span className="ml-2 text-xs text-gray-400">{c.industry}</span>
                                                    </div>
                                                    <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-primary transition-colors" />
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-700">업종 카테고리</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {['치과의원', '성형외과', '피부과', '기타'].map(opt => (
                                            <button
                                                key={opt}
                                                onClick={() => setIndustry(opt)}
                                                className={clsx(
                                                    "h-12 rounded-xl text-sm font-bold transition-all border",
                                                    industry === opt ? "bg-indigo-50 border-primary text-primary" : "bg-white border-gray-100 text-gray-500 hover:border-gray-200"
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
                                <h2 className="text-3xl font-bold text-gray-900 mb-2">분석 대상을 지정해주세요</h2>
                                <p className="text-gray-500">우리 병원과 비교하고 싶은 라이벌 병원을 등록합니다.</p>
                            </div>

                            {recentTargets.length > 0 && (
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <Sparkles className="w-4 h-4 text-primary" /> 추천/최근 병원 (퀵 셀렉트)
                                    </label>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                        {recentTargets.slice(0, 8).map(s => (
                                            <button
                                                key={s.id}
                                                onClick={() => handleSelectExistingTarget(s)}
                                                className="p-3 bg-white border border-gray-100 rounded-xl text-xs font-bold text-gray-600 hover:border-primary hover:bg-primary/5 hover:text-primary transition-all shadow-sm flex flex-col gap-1 text-left"
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

                            <div className="space-y-4 pt-6 border-t border-gray-50">
                                {targets.map((t, idx) => (
                                    <div key={idx} className={clsx(
                                        "p-6 rounded-2xl border transition-all flex items-center gap-4 relative overflow-visible",
                                        t.target_type === 'OWNER' ? "bg-indigo-50 border-indigo-100 ring-2 ring-primary/10" : "bg-white border-gray-100 shadow-sm"
                                    )}>
                                        <div className={clsx(
                                            "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0",
                                            t.target_type === 'OWNER' ? "bg-primary text-white" : "bg-gray-100 text-gray-500"
                                        )}>
                                            {t.target_type === 'OWNER' ? '나' : idx}
                                        </div>
                                        <div className="flex-1 grid grid-cols-2 gap-4">
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    placeholder="병원 이름"
                                                    value={t.name}
                                                    onFocus={() => setActiveTargetIdx(idx)}
                                                    onBlur={() => setTimeout(() => setActiveTargetIdx(null), 200)}
                                                    onChange={(e) => updateTarget(idx, 'name', e.target.value)}
                                                    className="w-full bg-transparent border-b border-gray-200 py-2 outline-none focus:border-primary font-bold transition-all"
                                                />
                                                {activeTargetIdx === idx && targetSuggestions.length > 0 && (
                                                    <div className="absolute top-[45px] left-0 w-full bg-white border border-gray-100 rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                        {targetSuggestions.map(s => (
                                                            <button
                                                                key={s.id}
                                                                onClick={() => {
                                                                    updateTarget(idx, 'name', s.name);
                                                                    updateTarget(idx, 'url', s.urls?.default || '');
                                                                    setTargetSuggestions([]);
                                                                }}
                                                                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between group transition-colors text-sm"
                                                            >
                                                                <span className="font-bold text-gray-700">{s.name}</span>
                                                                <LinkIcon className="w-3 h-3 text-gray-300" />
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <LinkIcon className="w-4 h-4 text-gray-400" />
                                                <input
                                                    type="url"
                                                    placeholder="네이버 플레이스 URL (선택)"
                                                    value={t.url}
                                                    onChange={(e) => updateTarget(idx, 'url', e.target.value)}
                                                    className="flex-1 bg-transparent border-b border-gray-100 py-2 outline-none focus:border-primary text-sm transition-all text-gray-500"
                                                />
                                            </div>
                                        </div>
                                        {t.target_type === 'COMPETITOR' && (
                                            <button onClick={() => removeTarget(idx)} className="text-gray-300 hover:text-red-500 transition-colors">
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        )}
                                    </div>
                                ))}
                                <button
                                    onClick={addTarget}
                                    className="w-full h-14 border-2 border-dashed border-gray-200 rounded-2xl flex items-center justify-center gap-2 text-gray-400 hover:border-primary hover:text-primary transition-all font-bold"
                                >
                                    <Plus className="w-5 h-5" /> 경쟁사 추가하기
                                </button>
                            </div>
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div>
                                <h2 className="text-3xl font-bold text-gray-900 mb-2">어떤 검색어로 조사할까요?</h2>
                                <p className="text-gray-500">마지막입니다! 분석하고 싶은 키워드와 매체를 선택하세요.</p>
                            </div>

                            <div className="space-y-10">
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-gray-700">조사 키워드</label>
                                    <div className="relative max-w-md">
                                        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                                        <input
                                            type="text"
                                            placeholder="예: 강남역 치과"
                                            value={keyword}
                                            onChange={(e) => setKeyword(e.target.value)}
                                            className="w-full h-16 bg-gray-50/50 border border-gray-100 rounded-2xl pl-12 pr-5 text-xl font-bold focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all outline-none shadow-sm"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-gray-700">분석 매체</label>
                                    <div className="flex gap-4">
                                        {[
                                            { id: 'NAVER_PLACE', name: '네이버 플레이스', color: 'bg-green-500' },
                                            { id: 'NAVER_VIEW', name: '네이버 VIEW(블로그)', color: 'bg-emerald-500' }
                                        ].map(p => (
                                            <button
                                                key={p.id}
                                                onClick={() => setPlatform(p.id)}
                                                className={clsx(
                                                    "px-6 py-4 rounded-2xl font-bold transition-all border flex items-center gap-3",
                                                    platform === p.id ? "bg-white border-primary text-primary shadow-lg shadow-primary/5" : "bg-gray-50 border-gray-100 text-gray-400"
                                                )}
                                            >
                                                <div className={clsx("w-2 h-2 rounded-full", p.color)} />
                                                {p.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {history.length > 0 && (
                                    <div className="space-y-4 pt-6 border-t border-gray-50">
                                        <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                            <History className="w-4 h-4 text-primary" /> 최근 분석 이력
                                        </label>
                                        <div className="flex flex-wrap gap-2">
                                            {history.map((h, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => selectHistory(h)}
                                                    className="px-4 py-2 bg-gray-50 border border-gray-100 rounded-full text-xs font-bold text-gray-600 hover:bg-primary hover:text-white hover:border-primary transition-all flex items-center gap-2 group"
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

                {/* Footer Buttons */}
                <div className="mt-12 flex items-center justify-between pt-8 border-t border-gray-50">
                    <button
                        disabled={currentStep === 1}
                        onClick={() => setCurrentStep(prev => prev > 1 ? (prev - 1) as Step : prev)}
                        className="flex items-center gap-2 text-gray-400 font-bold hover:text-gray-600 transition-colors disabled:opacity-0"
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
