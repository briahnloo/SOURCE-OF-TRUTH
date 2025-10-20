import { api } from '@/lib/api';
import EmptyState from '@/components/EmptyState';
import EventCard from '@/components/EventCard';

// Force dynamic rendering
export const dynamic = 'force-dynamic';

export default async function ConflictsPage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getConflicts({ limit: 50 });
        events = response.results;
    } catch (err) {
        error = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Error fetching conflicts:', err);
    }

    // Filter out irrelevant events (natural disasters, sports, entertainment)
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

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center space-y-4">
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white">
                    Conflicting Narratives
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
                    Political and social events where sources present significantly different stories or interpretations
                </p>

                {filteredCount > 0 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Showing {relevantEvents.length} events with political/social perspectives
                        {filteredCount > 0 && ` (filtered out ${filteredCount} natural disasters and sports)`}
                    </p>
                )}

                {/* Info Card */}
                <div className="card bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-700 text-left max-w-3xl mx-auto">
                    <div className="flex items-start space-x-3">
                        <span className="text-2xl">⚠️</span>
                        <div className="flex-1">
                            <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                                What this means
                            </h3>
                            <p className="text-sm text-yellow-800 dark:text-yellow-300">
                                These events have multiple interpretations or disputed facts. This
                                doesn&apos;t mean misinformation - just that sources disagree. We
                                recommend reading multiple perspectives to understand the full
                                context.
                            </p>
                            <ul className="mt-3 space-y-1 text-sm text-yellow-800 dark:text-yellow-300">
                                <li>• Different angles on the same story</li>
                                <li>• Developing situation with evolving details</li>
                                <li>• Legitimate debate or interpretation</li>
                                <li>• Need for careful reading from multiple sources</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Coherence Score Explanation */}
                <div className="card bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 dark:border-blue-700 text-left max-w-3xl mx-auto">
                    <div className="flex items-start space-x-3">
                        <span className="text-2xl">📊</span>
                        <div className="flex-1">
                            <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                                How we detect conflicts
                            </h3>
                            <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                                Each event gets a <strong>Coherence Score (0-100)</strong> that
                                measures how much sources agree on the narrative. Events below 80 are
                                flagged as conflicts.
                            </p>
                            <div className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                                <div>
                                    <strong>The score combines three factors:</strong>
                                </div>
                                <ul className="space-y-1 ml-4">
                                    <li>
                                        • <strong>Semantic similarity (60%)</strong> - How similar are
                                        the article contents?
                                    </li>
                                    <li>
                                        • <strong>Entity overlap (25%)</strong> - Do sources mention
                                        the same people, places, organizations?
                                    </li>
                                    <li>
                                        • <strong>Title consistency (15%)</strong> - Are headlines
                                        aligned on the story?
                                    </li>
                                </ul>
                                <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
                                    <strong>Conflict severity levels:</strong>
                                    <ul className="space-y-1 ml-4 mt-1">
                                        <li>• <strong>High (0-39)</strong> - Major disagreements</li>
                                        <li>• <strong>Medium (40-59)</strong> - Significant differences</li>
                                        <li>• <strong>Low (60-79)</strong> - Minor variations</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Events */}
            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400">
                    <p className="text-red-800 dark:text-red-300">⚠️ {error}</p>
                </div>
            ) : relevantEvents.length > 0 ? (
                <div className="space-y-6">
                    {relevantEvents.map((event) => (
                        <EventCard key={event.id} event={event} />
                    ))}
                </div>
            ) : (
                <EmptyState
                    title="No Conflicting Events"
                    message="All recent political and social events show consistent narratives across sources. Check back later."
                />
            )}
        </div>
    );
}
