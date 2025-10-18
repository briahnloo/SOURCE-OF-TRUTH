'use client';

import { StatsResponse } from '@/lib/api';
import { useEffect, useState } from 'react';

interface StatsPanelProps {
    stats: StatsResponse;
}

function AnimatedNumber({ value }: { value: number }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const duration = 1000;
        const steps = 30;
        const increment = value / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                setCount(value);
                clearInterval(timer);
            } else {
                setCount(Math.floor(current));
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [value]);

    return <span className="tabular-nums">{count.toLocaleString()}</span>;
}

export default function StatsPanel({ stats }: StatsPanelProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Events */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Total Events
                        </div>
                        <div className="mt-2 text-4xl font-bold text-gray-900 dark:text-white">
                            <AnimatedNumber value={stats.total_events} />
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">📊</div>
                </div>
            </div>

            {/* Confirmed */}
            <div className="card bg-gradient-to-br from-confirmed-50 to-white dark:from-confirmed-900/20 dark:to-gray-900 border-l-4 border-confirmed hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-confirmed-dark dark:text-confirmed-light uppercase tracking-wide">
                            Confirmed
                        </div>
                        <div className="mt-2 text-4xl font-bold text-confirmed-dark dark:text-confirmed-light">
                            <AnimatedNumber value={stats.confirmed_events} />
                        </div>
                    </div>
                    <div className="text-4xl">✓</div>
                </div>
            </div>

            {/* Developing */}
            <div className="card bg-gradient-to-br from-developing-50 to-white dark:from-developing-900/20 dark:to-gray-900 border-l-4 border-developing hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-developing-dark dark:text-developing-light uppercase tracking-wide">
                            Developing
                        </div>
                        <div className="mt-2 text-4xl font-bold text-developing-dark dark:text-developing-light">
                            <AnimatedNumber value={stats.developing_events} />
                        </div>
                    </div>
                    <div className="text-4xl">🔄</div>
                </div>
            </div>

            {/* Underreported */}
            <div className="card bg-gradient-to-br from-underreported-50 to-white dark:from-underreported-900/20 dark:to-gray-900 border-l-4 border-underreported hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-underreported-dark dark:text-underreported-light uppercase tracking-wide">
                            Underreported
                        </div>
                        <div className="mt-2 text-4xl font-bold text-underreported-dark dark:text-underreported-light">
                            <AnimatedNumber value={stats.underreported_events} />
                        </div>
                    </div>
                    <div className="text-4xl">📢</div>
                </div>
            </div>

            {/* Avg Score */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Avg Confidence
                        </div>
                        <div className="mt-2 text-4xl font-bold text-gray-900 dark:text-white tabular-nums">
                            {stats.avg_confidence_score.toFixed(1)}
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">⭐</div>
                </div>
            </div>

            {/* Total Articles */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Total Articles
                        </div>
                        <div className="mt-2 text-4xl font-bold text-gray-900 dark:text-white">
                            <AnimatedNumber value={stats.total_articles} />
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">📰</div>
                </div>
            </div>

            {/* Sources Count */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Unique Sources
                        </div>
                        <div className="mt-2 text-4xl font-bold text-gray-900 dark:text-white">
                            <AnimatedNumber value={stats.sources_count} />
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">🔗</div>
                </div>
            </div>

            {/* Last Ingestion */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Last Update
                        </div>
                        <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                            {stats.last_ingestion
                                ? new Date(stats.last_ingestion).toLocaleTimeString()
                                : 'N/A'}
                        </div>
                        <div className="mt-1 flex items-center space-x-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-xs text-gray-500">Live</span>
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">⏱️</div>
                </div>
            </div>
        </div>
    );
}
