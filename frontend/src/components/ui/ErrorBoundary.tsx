'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    /** 에러 발생 시 보여줄 컴포넌트 이름 (디버깅용) */
    name?: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * 위젯/섹션 레벨 에러 바운더리
 * 특정 컴포넌트가 크래시해도 나머지 페이지는 정상 동작
 *
 * 사용 예시:
 * <ErrorBoundary name="ROAS 차트">
 *   <RoasChart data={data} />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        console.error(
            `[ErrorBoundary${this.props.name ? `:${this.props.name}` : ''}]`,
            error,
            info.componentStack
        );
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            // 커스텀 폴백이 제공된 경우
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // 기본 폴백 UI
            return (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center">
                    <div className="flex items-center justify-center gap-2 text-amber-600 mb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-sm font-medium">
                            {this.props.name
                                ? `'${this.props.name}' 컴포넌트 오류`
                                : '컴포넌트를 불러오지 못했습니다'}
                        </span>
                    </div>
                    {process.env.NODE_ENV === 'development' && this.state.error && (
                        <p className="text-xs text-amber-500 mb-3 font-mono truncate">
                            {this.state.error.message}
                        </p>
                    )}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={this.handleReset}
                        className="gap-1.5 text-xs border-amber-300 text-amber-700 hover:bg-amber-100"
                    >
                        <RefreshCw className="w-3 h-3" />
                        다시 시도
                    </Button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
