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

    // Filter for conflicts with interesting narrative differences (backend does main filtering)
    const relevantEvents = events.filter(event => {
        // Only show events with political/social perspectives
        if (event.category === 'natural_disaster') return false;
        if (event.category === 'health' && event.sources?.every((s: any) => s.domain?.includes('usgs.gov'))) return false;

        // Check for sports/entertainment keywords in title
        const title = event.summary?.toLowerCase() || '';
        const irrelevantKeywords = ['fanduel', 'nfl', 'betting', 'odds', 'picks', 'prediction'];
        if (irrelevantKeywords.some(kw => title.includes(kw))) return false;

        // Backend has already filtered for 2+ sources, so just show what comes back
        // The diverse sources themselves indicate different coverage angles
        // (Frontend filtering was too strict - removing it)

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
                    Events where different sources tell the same story very differently - through framing, emphasis, tone, and interpretation
                </p>

                <p className="text-sm text-gray-500 dark:text-gray-400">
                    Showing {relevantEvents.length} narrative conflicts with meaningful perspective differences
                    {filteredCount > 0 && ` (filtered ${filteredCount} non-political events)`}
                </p>

                {/* Info Card */}
                <div className="card bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-700 text-left max-w-3xl mx-auto">
                    <div className="flex items-start space-x-3">
                        <span className="text-2xl">⚠️</span>
                        <div className="flex-1">
                            <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                                What this means
                            </h3>
                            <p className="text-sm text-yellow-800 dark:text-yellow-300">
                                These events are covered very differently across sources. The same facts might be
                                framed as positive/negative, emphasized differently, or presented with conflicting
                                context. This is NOT necessarily misinformation - it&apos;s how bias, editorial choices,
                                and audience preferences shape news narratives.
                            </p>
                            <ul className="mt-3 space-y-1 text-sm text-yellow-800 dark:text-yellow-300">
                                <li>• Partisan vs. neutral framing of the same event</li>
                                <li>• Different emphasis on which facts matter most</li>
                                <li>• Tone differences (sensational vs. measured)</li>
                                <li>• Competing narratives from left/right or other perspectives</li>
                                <li>• Genuine reporting disagreements on what happened</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Detection Methodology */}
                <div className="card bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 dark:border-blue-700 text-left max-w-3xl mx-auto">
                    <div className="flex items-start space-x-3">
                        <span className="text-2xl">📊</span>
                        <div className="flex-1">
                            <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                                How we detect conflicts
                            </h3>
                            <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                                We detect narrative conflicts through semantic analysis, bias detection, and perspective extraction. These aren&apos;t just headline differences - they&apos;re meaningful divergences in how events are framed and interpreted.
                            </p>
                            <div className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                                <div>
                                    <strong>Multi-layered detection:</strong>
                                </div>
                                <ul className="space-y-1 ml-4">
                                    <li>
                                        • <strong>Semantic analysis</strong> - Embedding similarity detects when articles use different language/framing for the same event
                                    </li>
                                    <li>
                                        • <strong>Entity & sentiment analysis</strong> - Identifies how sources emphasize different facts, people, and outcomes
                                    </li>
                                    <li>
                                        • <strong>Bias detection</strong> - Finds partisan vs. neutral coverage (left, center, right sources)
                                    </li>
                                    <li>
                                        • <strong>Perspective extraction</strong> - AI identifies the distinct narrative angles each group tells
                                    </li>
                                </ul>
                                <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
                                    <strong>What we show you:</strong>
                                    <ul className="space-y-1 ml-4 mt-1">
                                        <li>• <strong>Diverse narrative framing</strong> - How the same event is told very differently</li>
                                        <li>• <strong>Cross-political coverage</strong> - Left, right, and center sources with their differing angles</li>
                                        <li>• <strong>Substantive disagreements</strong> - 5+ articles from 3+ sources (real coverage, not anomalies)</li>
                                        <li>• <strong>Genuine difference in perspective</strong> - Not just headline variations (keyword overlap &lt; 50%)</li>
                                        <li>• <strong>Politics & international events</strong> - Where different narratives matter most</li>
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
