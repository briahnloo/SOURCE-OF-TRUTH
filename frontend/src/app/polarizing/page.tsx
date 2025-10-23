import { api } from '@/lib/api';
import PolarizingSourceCard from '@/components/PolarizingSourceCard';
import EmptyState from '@/components/EmptyState';

// Force dynamic rendering
export const dynamic = 'force-dynamic';

export default async function PolarizingPage() {
    let sources: any[] = [];
    let methodology = '';
    let error: string | null = null;

    try {
        const response = await api.getPolarizingSources({ limit: 50 });
        sources = response.sources;
        methodology = response.methodology;
    } catch (err) {
        error = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Error fetching polarizing sources:', err);
    }

    return (
        <div className="min-h-screen">
            {/* Header */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="text-center space-y-6 mb-12">
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white">
                        Most Polarizing News Sources
                    </h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
                        News sources ranked by political rhetoric polarization, showing their most inflammatory headlines.
                        Each excerpt is scored by keyword analysis - identifying words like &quot;illegal&quot;, &quot;radical&quot;, &quot;slams&quot;, and &quot;crisis&quot;.
                    </p>

                    {/* Methodology Card */}
                    <div className="card bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 dark:border-blue-700 text-left max-w-4xl mx-auto">
                        <div className="flex items-start space-x-3">
                            <span className="text-2xl">📊</span>
                            <div className="flex-1">
                                <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                                    How Polarization is Calculated
                                </h3>
                                <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                                    {methodology}
                                </p>
                                <div className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
                                    <p><strong>Source-Level Score (60% political extremity + 40% sensationalism):</strong> Distance from political center combined with tone analysis. Treats left and right extremity equally.</p>
                                    <p><strong>Excerpt-Level Scoring:</strong> Each headline is analyzed for inflammatory keywords:</p>
                                    <ul className="ml-4 space-y-1">
                                        <li>• High intensity (3 pts): &quot;illegal&quot;, &quot;radical&quot;, &quot;racist&quot;, &quot;scandal&quot;, &quot;corrupt&quot;, &quot;disaster&quot;</li>
                                        <li>• Medium intensity (2 pts): &quot;slams&quot;, &quot;blasts&quot;, &quot;demands&quot;, &quot;condemns&quot;, &quot;backlash&quot;</li>
                                        <li>• Low intensity (1 pt): &quot;questions&quot;, &quot;concerns&quot;, &quot;challenges&quot;, &quot;debate&quot;</li>
                                        <li>• Bonus for exclamation marks, ALL CAPS, and quoted inflammatory phrases</li>
                                    </ul>
                                    <p className="pt-2 border-t border-blue-200 dark:border-blue-800">
                                        <strong>What You See:</strong> The most polarizing headlines from each source, ranked by keyword intensity.
                                        Political content only - sports and entertainment filtered out.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* What This Means Card */}
                    <div className="card bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-700 text-left max-w-4xl mx-auto">
                        <div className="flex items-start space-x-3">
                            <span className="text-2xl">💡</span>
                            <div className="flex-1">
                                <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                                    Why This Matters
                                </h3>
                                <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
                                    Understanding which sources use more polarizing rhetoric helps you make informed decisions about your news consumption.
                                </p>
                                <ul className="space-y-1 text-sm text-yellow-800 dark:text-yellow-300">
                                    <li>• <strong>Headlines reveal bias</strong> - How sources frame the same story differently</li>
                                    <li>• <strong>Keyword patterns</strong> - Words like &quot;illegal&quot;, &quot;radical&quot;, &quot;slams&quot; indicate emotional framing vs factual reporting</li>
                                    <li>• <strong>Scored by intensity</strong> - Each headline gets a 0-100 polarization score based on inflammatory language</li>
                                    <li>• <strong>Political content only</strong> - Sports and entertainment articles filtered out to focus on political rhetoric</li>
                                    <li>• <strong>See the evidence</strong> - Highlighted keywords show exactly what makes each headline polarizing</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {sources.length > 0 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Showing {sources.length} sources ranked by polarization score
                        </p>
                    )}
                </div>

                {/* Sources List */}
                {error ? (
                    <div className="card bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400">
                        <p className="text-red-800 dark:text-red-300">⚠️ {error}</p>
                    </div>
                ) : sources.length > 0 ? (
                    <div className="space-y-6 max-w-5xl mx-auto">
                        {sources.map((source, idx) => (
                            <PolarizingSourceCard key={source.domain} source={source} rank={idx + 1} />
                        ))}
                    </div>
                ) : (
                    <EmptyState
                        title="No Sources Available"
                        message="Not enough data to calculate polarization rankings. Check back later as more articles are ingested."
                    />
                )}
            </div>
        </div>
    );
}

