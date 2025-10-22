'use client';

import { useState } from 'react';
import { Event } from '@/lib/api';
import EventCard from '@/components/EventCard';
import EmptyState from '@/components/EmptyState';

interface Props {
    events: Event[];
    error: string | null;
}

export default function DevelopingPageClient({ events, error }: Props) {
    const [showGuide, setShowGuide] = useState(true);

    // Sort events by most recent first (chronological order)
    const sortedEvents = [...events].sort((a, b) => {
        const dateA = new Date(a.first_seen).getTime();
        const dateB = new Date(b.first_seen).getTime();
        return dateB - dateA; // Most recent first
    });

    // Calculate perspective stats
    const leftCount = events.filter(e =>
        e.sources?.some(s => s.political_bias && s.political_bias.left > s.political_bias.center && s.political_bias.left > s.political_bias.right)
    ).length;

    const rightCount = events.filter(e =>
        e.sources?.some(s => s.political_bias && s.political_bias.right > s.political_bias.center && s.political_bias.right > s.political_bias.left)
    ).length;

    const conflictCount = events.filter(e => e.has_conflict).length;

    return (
        <div className="min-h-screen">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="mb-6">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                        Developing Events
                    </h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400">
                        Events with moderate coverage (scores 40-74) currently being verified
                    </p>
                </div>

                {/* Collapsible Guide */}
                {showGuide && (
                    <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg shadow-sm">
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <span className="text-xl">📋</span>
                                <h3 className="font-semibold text-blue-900 dark:text-blue-200">
                                    About Developing Events
                                </h3>
                            </div>
                            <button
                                onClick={() => setShowGuide(false)}
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 text-sm font-medium"
                            >
                                Hide guide
                            </button>
                        </div>
                        <div className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                            <p>
                                These stories have 5-10 sources and are being actively verified.
                                Scores of 40-74 mean moderate confidence. Look for:
                            </p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Perspective differences (how left/right frame the story)</li>
                                <li>Missing official confirmation</li>
                                <li>Numerical disagreements between sources</li>
                            </ul>
                            <p className="mt-3 font-medium">
                                💡 Tip: Read articles from multiple perspectives to understand the full story
                            </p>
                        </div>
                    </div>
                )}

                {/* Stats Bar */}
                {events.length > 0 && (
                    <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                            <span className="font-semibold text-gray-700 dark:text-gray-300">
                                {events.length} developing events (sorted by most recent)
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
                ) : sortedEvents.length === 0 ? (
                    <EmptyState
                        title="No developing events at this time"
                        message="Events in this tier have moderate source coverage and are being actively verified. They may be promoted to Confirmed as more sources report."
                    />
                ) : (
                    <div className="space-y-6 animate-fade-in">
                        {sortedEvents.map((event, idx) => (
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
                        className="mt-6 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                        Show guide
                    </button>
                )}
            </div>
        </div>
    );
}
