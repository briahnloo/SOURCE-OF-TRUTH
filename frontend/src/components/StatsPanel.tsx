'use client';

import { StatsResponse } from '@/lib/api';
import { useEffect, useState } from 'react';

interface StatsPanelProps {
    stats: StatsResponse;
}

function AnimatedNumber({ value }: { value: number }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        // Reset count when value changes
        setCount(0);

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
    const [timeAgo, setTimeAgo] = useState<string>('');

    useEffect(() => {
        const updateTimeAgo = () => {
            if (!stats.last_ingestion) {
                setTimeAgo('N/A');
                return;
            }

            const now = new Date();
            const lastUpdate = new Date(stats.last_ingestion);
            const diffMs = now.getTime() - lastUpdate.getTime();
            const diffSeconds = Math.floor(diffMs / 1000);
            const diffMinutes = Math.floor(diffSeconds / 60);
            const diffHours = Math.floor(diffMinutes / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffSeconds < 60) {
                setTimeAgo(`${diffSeconds} second${diffSeconds !== 1 ? 's' : ''} ago`);
            } else if (diffMinutes < 60) {
                setTimeAgo(`${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`);
            } else if (diffHours < 24) {
                setTimeAgo(`${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`);
            } else {
                setTimeAgo(`${diffDays} day${diffDays !== 1 ? 's' : ''} ago`);
            }
        };

        // Update immediately
        updateTimeAgo();

        // Update every second
        const interval = setInterval(updateTimeAgo, 1000);

        return () => clearInterval(interval);
    }, [stats.last_ingestion]);

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
                            <span className="tabular-nums">{stats.total_events.toLocaleString()}</span>
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
                            <span className="tabular-nums">{stats.confirmed_events.toLocaleString()}</span>
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
                            <span className="tabular-nums">{stats.developing_events.toLocaleString()}</span>
                        </div>
                    </div>
                    <div className="text-4xl">🔄</div>
                </div>
            </div>

            {/* Conflicts */}
            <div className="card bg-gradient-to-br from-yellow-50 to-white dark:from-yellow-900/20 dark:to-gray-900 border-l-4 border-yellow-500 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-yellow-700 dark:text-yellow-400 uppercase tracking-wide">
                            Conflicting Narratives
                        </div>
                        <div className="mt-2 text-4xl font-bold text-yellow-700 dark:text-yellow-400">
                            <span className="tabular-nums">{stats.conflict_events.toLocaleString()}</span>
                        </div>
                    </div>
                    <div className="text-4xl">⚠️</div>
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
                            <span className="tabular-nums">{stats.total_articles.toLocaleString()}</span>
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
                            <span className="tabular-nums">{stats.sources_count.toLocaleString()}</span>
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">🔗</div>
                </div>
            </div>

            {/* Last Ingestion */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div className="w-full">
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Last Update
                        </div>
                        <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                            {stats.last_ingestion
                                ? (() => {
                                    const date = new Date(stats.last_ingestion);
                                    const timeString = date.toLocaleTimeString('en-US', {
                                        timeZone: 'America/Los_Angeles',
                                        hour: 'numeric',
                                        minute: '2-digit',
                                        second: '2-digit',
                                        hour12: true
                                    });
                                    return `${timeString} PST`;
                                })()
                                : 'N/A'}
                        </div>
                        <div className="mt-2 flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                                    {timeAgo}
                                </span>
                            </div>
                            <span className="text-xs text-gray-500">Live</span>
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">⏱️</div>
                </div>
            </div>
        </div>
    );
}
