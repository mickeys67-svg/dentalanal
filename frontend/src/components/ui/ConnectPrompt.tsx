"use client";

import { PlugZap } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * 데이터 연동 안내 (ConnectPrompt)
 *
 * 값이 없는 빈 영역이 "연동 미완료" 때문일 때 표시하는 전문 안내 컴포넌트.
 * ⚠️ 가짜 데이터 금지: 수치를 지어내지 않고, 연동 시 실측값이 표출됨을 안내한다.
 *
 * 사용 예:
 *   <ConnectPrompt source="YouTube Data API" />
 *   <ConnectPrompt title="감성 분석 미연동" source="감성 분석 엔진" compact />
 */
interface ConnectPromptProps {
    /** 연동 대상 소스명 (예: "YouTube Data API", "Meta 광고 계정") */
    source?: string;
    /** 상단 제목. 미지정 시 "데이터 연동 필요" */
    title?: string;
    /** 본문 문구를 직접 지정하고 싶을 때 (미지정 시 source 기반 기본 문구) */
    description?: string;
    /** 연동 경로 안내 문구 (예: "[데이터 수집] 메뉴") */
    actionHint?: string;
    /** 좁은 영역용 소형 레이아웃 */
    compact?: boolean;
    className?: string;
}

export function ConnectPrompt({
    source = "데이터 소스",
    title = "데이터 연동 필요",
    description,
    actionHint,
    compact = false,
    className,
}: ConnectPromptProps) {
    const body =
        description ??
        `고객님의 ${source} 연동 시 실측 데이터가 자동으로 표출됩니다.`;

    return (
        <div
            className={cn(
                "w-full h-full flex flex-col items-center justify-center text-center",
                "rounded-xl border border-dashed border-slate-200 bg-slate-50/60",
                compact ? "px-4 py-6 gap-1.5" : "px-6 py-10 gap-2",
                className
            )}
        >
            <div
                className={cn(
                    "rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-500 mb-1",
                    compact ? "w-9 h-9" : "w-11 h-11"
                )}
            >
                <PlugZap className={compact ? "w-4 h-4" : "w-5 h-5"} />
            </div>
            <p className={cn("font-semibold text-slate-700", compact ? "text-sm" : "text-base")}>
                {title}
            </p>
            <p className={cn("text-slate-500 leading-relaxed max-w-xs", compact ? "text-xs" : "text-sm")}>
                {body}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
                연동 전까지는 데이터 정확성을 위해 수치를 표시하지 않습니다.
            </p>
            {actionHint && (
                <p className="text-[11px] font-medium text-indigo-500 mt-1">
                    연동 경로: {actionHint}
                </p>
            )}
        </div>
    );
}
