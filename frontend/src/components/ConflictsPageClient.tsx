'use client';

import { useState } from 'react';
import { Event } from '@/lib/api';
import EventCard from '@/components/EventCard';
import EmptyState from '@/components/EmptyState';

interface Props {
    events: Event[];
    error: string | null;
}

export default function ConflictsPageClient({ events, error }: Props) {
    const [showGuide, setShowGuide] = useState(true);

    // Filter for conflicts with interesting narrative differences
    const relevantEvents = events.filter(event => {
        // Only show events with political/social perspectives
        if (event.category === 'natural_disaster') return false;
        if (event.category === 'health' && event.sources?.every((s: any) => s.domain?.includes('usgs.gov'))) return false;

        // Check for sports/entertainment keywords in title
        const title = event.summary?.toLowerCase() || '';
        const irrelevantKeywords = ['fanduel', 'nfl', 'betting', 'odds', 'picks', 'prediction'];
        if (irrelevantKeywords.some(kw => title.includes(kw))) return false;

        return true;
    });

    const filteredCount = events.length - relevantEvents.length;

    // Calculate perspective stats
    const leftCount = relevantEvents.filter(e =>
        e.sources?.some(s => s.political_bias && s.political_bias.left > s.political_bias.center && s.political_bias.left > s.political_bias.right)
    ).length;

    const rightCount = relevantEvents.filter(e =>
        e.sources?.some(s => s.political_bias && s.political_bias.right > s.political_bias.center && s.political_bias.right > s.political_bias.left)
    ).length;

    const conflictCount = relevantEvents.filter(e => e.has_conflict).length;

    return (
        <div className="min-h-screen">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="mb-6">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                        Conflicting Narratives
                    </h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400">
                        Events where different sources tell the same story very differently - through framing, emphasis, tone, and interpretation
                    </p>
                </div>

                {/* Collapsible Guide */}
                {showGuide && (
                    <div className="mb-6 space-y-4">
                        {/* Main Info Card */}
                        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg shadow-sm">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <span className="text-xl">⚠️</span>
                                    <h3 className="font-semibold text-yellow-900 dark:text-yellow-200">
                                        What this means
                                    </h3>
                                </div>
                                <button
                                    onClick={() => setShowGuide(false)}
                                    className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200 text-sm font-medium"
                                >
                                    Hide guide
                                </button>
                            </div>
                            <div className="text-sm text-yellow-800 dark:text-yellow-300 space-y-3">
                                <p>
                                    These events are covered very differently across sources—same facts, different
                                    angles. That&apos;s normal reporting. Different outlets emphasize different details,
                                    frame events differently, or focus on different aspects of the story.
                                </p>
                                <div>
                                    <strong>Examples:</strong>
                                    <ul className="list-disc list-inside space-y-1 ml-2 mt-1">
                                        <li>Partisan vs neutral framing</li>
                                        <li>Different emphasis on which facts matter</li>
                                        <li>Tone shifts (cautious vs sensational)</li>
                                        <li>Conflicting narratives</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Detection Methodology */}
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg shadow-sm">
                            <div className="flex items-start space-x-3">
                                <span className="text-xl">📊</span>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                                        How we detect this
                                    </h3>
                                    <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                                        We detect real conflicts by comparing how different sources cover the same event.
                                        We look for:
                                    </p>
                                    <ul className="list-disc list-inside space-y-1 ml-2 text-sm text-blue-800 dark:text-blue-300">
                                        <li>Different wording and perspective</li>
                                        <li>What each source emphasizes</li>
                                        <li>Political perspective of sources (left, center, right)</li>
                                        <li>Different story angles and framings</li>
                                    </ul>
                                    <p className="text-sm text-blue-800 dark:text-blue-300 mt-3">
                                        We only flag events with real differences—multiple major sources
                                        showing truly different viewpoints, not just variations in wording.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Stats Bar */}
                {relevantEvents.length > 0 && (
                    <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                            <span className="font-semibold text-gray-700 dark:text-gray-300">
                                {relevantEvents.length} narrative conflicts with meaningful perspective differences
                                {filteredCount > 0 && ` (filtered ${filteredCount} non-political events)`}
                            </span>
                            {leftCount > 0 && (
                                <>
                                    <span className="text-gray-500">•</span>
                                    <span className="text-gray-600 dark:text-gray-400">
                                        🔵 {leftCount} with liberal coverage
                                    </span>
                                </>
                            )}
                            {rightCount > 0 && (
                                <>
                                    <span className="text-gray-500">•</span>
                                    <span className="text-gray-600 dark:text-gray-400">
                                        🔴 {rightCount} with conservative coverage
                                    </span>
                                </>
                            )}
                            {conflictCount > 0 && (
                                <>
                                    <span className="text-gray-500">•</span>
                                    <span className="text-gray-600 dark:text-gray-400">
                                        ⚠️ {conflictCount} with perspective conflicts
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {error ? (
                    <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                        <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                    </div>
                ) : relevantEvents.length === 0 ? (
                    <EmptyState
                        title="No Conflicting Events"
                        message="All recent political and social events show consistent narratives across sources. Check back later."
                    />
                ) : (
                    <div className="space-y-6 animate-fade-in">
                        {relevantEvents.map((event, idx) => (
                            <div
                                key={event.id}
                                style={{ animationDelay: `${idx * 0.05}s` }}
                                className="animate-slide-up"
                            >
                                <EventCard event={event} />
                            </div>
                        ))}
                    </div>
                )}

                {!showGuide && (
                    <button
                        onClick={() => setShowGuide(true)}
                        className="mt-6 text-sm text-yellow-600 dark:text-yellow-400 hover:underline"
                    >
                        Show guide
                    </button>
                )}
            </div>
        </div>
    );
}
