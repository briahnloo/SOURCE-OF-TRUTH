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
    const [timeAgo, setTimeAgo] = useState<string>('Calculating...');

    useEffect(() => {
        const updateTimeAgo = () => {
            if (!stats || !stats.last_ingestion) {
                setTimeAgo('No data');
                return;
            }

            try {
                const now = new Date();

                // BUGFIX: Handle timezone-aware parsing
                // If timestamp doesn't have timezone indicator (Z or ±HH:MM), add 'Z' to parse as UTC
                let timestampStr = stats.last_ingestion;
                if (timestampStr && !timestampStr.endsWith('Z') && !timestampStr.match(/[+-]\d{2}:\d{2}$/)) {
                    // Naive timestamp - append Z to indicate UTC
                    timestampStr = timestampStr + 'Z';
                }

                const lastUpdate = new Date(timestampStr || stats.last_ingestion);

                // Handle invalid dates
                if (isNaN(lastUpdate.getTime())) {
                    setTimeAgo('Invalid timestamp');
                    return;
                }

                // Calculate time difference in milliseconds
                const diffMs = now.getTime() - lastUpdate.getTime();

                // DEBUG: Log the calculation for verification
                console.debug('Last Update Debug:', {
                    now: now.toISOString(),
                    lastUpdate: lastUpdate.toISOString(),
                    lastUpdateInput: stats.last_ingestion,
                    diffMs: diffMs,
                    diffSeconds: Math.floor(diffMs / 1000),
                });

                // Handle negative time (future timestamp - shouldn't happen but catch it)
                if (diffMs < 0) {
                    console.warn('Future timestamp detected:', { diffMs, now, lastUpdate });
                    setTimeAgo('Just now');
                    return;
                }

                const diffSeconds = Math.floor(diffMs / 1000);
                const diffMinutes = Math.floor(diffSeconds / 60);
                const diffHours = Math.floor(diffMinutes / 60);
                const diffDays = Math.floor(diffHours / 24);

                // Display with appropriate granularity
                if (diffSeconds < 10) {
                    setTimeAgo('Just now');
                } else if (diffSeconds < 60) {
                    setTimeAgo(`${diffSeconds} second${diffSeconds !== 1 ? 's' : ''} ago`);
                } else if (diffMinutes < 60) {
                    setTimeAgo(`${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`);
                } else if (diffHours < 24) {
                    setTimeAgo(`${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`);
                } else {
                    setTimeAgo(`${diffDays} day${diffDays !== 1 ? 's' : ''} ago`);
                }
            } catch (error) {
                console.error('Error calculating time ago:', error);
                setTimeAgo('Error');
            }
        };

        // Update immediately
        updateTimeAgo();

        // Update every second for real-time feel
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

            {/* Last Update - Shows when data was last refreshed */}
            <div className="card bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:scale-105 transition-transform duration-200">
                <div className="flex items-center justify-between">
                    <div className="w-full">
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Last Update
                        </div>

                        {/* Main Display: Time Ago (e.g., "2 minutes ago") */}
                        <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                            {timeAgo || 'N/A'}
                        </div>

                        {/* Secondary Display: Actual time in PST (e.g., "2:30 PM PST") */}
                        <div className="mt-1 text-xs text-gray-600 dark:text-gray-500">
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
                                : 'No data'}
                        </div>

                        {/* Status Indicator */}
                        <div className="mt-2 flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-xs text-gray-500 dark:text-gray-400">Live</span>
                        </div>
                    </div>
                    <div className="text-4xl opacity-20">⏱️</div>
                </div>
            </div>
        </div>
    );
}
