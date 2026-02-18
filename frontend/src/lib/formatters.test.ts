import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { timeAgo, getRankDropSeverity, getOverlapLevel, formatKRW } from './formatters';

describe('timeAgo', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-02-19T12:00:00Z'));
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('30초 전 → 방금 전', () => {
        const date = new Date('2026-02-19T11:59:30Z').toISOString();
        expect(timeAgo(date)).toBe('방금 전');
    });

    it('5분 전 → 5분 전', () => {
        const date = new Date('2026-02-19T11:55:00Z').toISOString();
        expect(timeAgo(date)).toBe('5분 전');
    });

    it('59분 전 → 59분 전', () => {
        const date = new Date('2026-02-19T11:01:00Z').toISOString();
        expect(timeAgo(date)).toBe('59분 전');
    });

    it('2시간 전 → 2시간 전', () => {
        const date = new Date('2026-02-19T10:00:00Z').toISOString();
        expect(timeAgo(date)).toBe('2시간 전');
    });

    it('1일 전 → 1일 전', () => {
        const date = new Date('2026-02-18T12:00:00Z').toISOString();
        expect(timeAgo(date)).toBe('1일 전');
    });

    it('3일 전 → 3일 전', () => {
        const date = new Date('2026-02-16T12:00:00Z').toISOString();
        expect(timeAgo(date)).toBe('3일 전');
    });
});

describe('getRankDropSeverity', () => {
    it('10위 이상 하락 → high', () => {
        expect(getRankDropSeverity(10)).toBe('high');
        expect(getRankDropSeverity(15)).toBe('high');
    });

    it('5~9위 하락 → medium', () => {
        expect(getRankDropSeverity(5)).toBe('medium');
        expect(getRankDropSeverity(9)).toBe('medium');
    });

    it('1~4위 하락 → low', () => {
        expect(getRankDropSeverity(1)).toBe('low');
        expect(getRankDropSeverity(4)).toBe('low');
    });

    it('0 → low', () => {
        expect(getRankDropSeverity(0)).toBe('low');
    });
});

describe('getOverlapLevel', () => {
    it('0.7 이상 → danger', () => {
        expect(getOverlapLevel(0.7)).toBe('danger');
        expect(getOverlapLevel(1.0)).toBe('danger');
    });

    it('0.4 이상 0.7 미만 → warning', () => {
        expect(getOverlapLevel(0.4)).toBe('warning');
        expect(getOverlapLevel(0.69)).toBe('warning');
    });

    it('0.4 미만 → low', () => {
        expect(getOverlapLevel(0.0)).toBe('low');
        expect(getOverlapLevel(0.39)).toBe('low');
    });
});

describe('formatKRW', () => {
    it('억 단위 포맷', () => {
        expect(formatKRW(100_000_000)).toBe('1.0억원');
        expect(formatKRW(250_000_000)).toBe('2.5억원');
    });

    it('만 단위 포맷', () => {
        expect(formatKRW(50_000)).toBe('5만원');
        expect(formatKRW(120_000)).toBe('12만원');
    });

    it('1만 미만 포맷', () => {
        expect(formatKRW(9_999)).toBe('9,999원');
        expect(formatKRW(0)).toBe('0원');
    });
});
