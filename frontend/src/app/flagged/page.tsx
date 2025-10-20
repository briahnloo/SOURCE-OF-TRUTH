import { api } from '@/lib/api';
import EmptyState from '@/components/EmptyState';
import FlaggedArticleCard from '@/components/FlaggedArticleCard';
import SourceErrorRates from '@/components/SourceErrorRates';

export const dynamic = 'force-dynamic';

export default async function FlaggedPage() {
    let data: any = null;
    let error: string | null = null;

    try {
        data = await api.getFlaggedArticles({ limit: 50 });
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch flagged articles';
        console.error('Error fetching flagged articles:', e);
    }

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 flex items-center space-x-2">
                    <span>🚨</span>
                    <span>Fact-Check Failures</span>
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                    Articles containing claims that contradict official data or have been debunked by
                    fact-checkers
                </p>
            </div>

            {/* Summary Stats */}
            {data && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="card text-center bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                        <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                            {data.summary.false || 0}
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                            False Claims
                        </p>
                    </div>
                    <div className="card text-center bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
                        <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                            {data.summary.disputed || 0}
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                            Disputed Claims
                        </p>
                    </div>
                    <div className="card text-center bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
                        <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                            {data.summary.total_flagged || 0}
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                            Total Flagged
                        </p>
                    </div>
                    <div className="card text-center bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                        <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                            {data.summary.total_checked || 0}
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                            Articles Checked (last 30 days)
                        </p>
                    </div>
                </div>
            )}

            {/* Methodology Card */}
            <div className="card bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 mb-6">
                <h3 className="text-md font-semibold text-blue-900 dark:text-blue-200 mb-2">
                    How We Fact-Check
                </h3>
                <div className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                    <p>
                        We verify article claims using multiple authoritative sources:
                    </p>
                    <ul className="space-y-1 ml-5 list-disc">
                        <li>
                            <strong>Google Fact Check API</strong> - Aggregates fact-checks from
                            PolitiFact, Snopes, FactCheck.org, AP Fact Check
                        </li>
                        <li>
                            <strong>Official Government Sources</strong> - USGS (earthquakes), WHO
                            (disease outbreaks), NASA (wildfires)
                        </li>
                        <li>
                            <strong>Cross-Reference Verification</strong> - Comparing claims across
                            multiple sources
                        </li>
                    </ul>
                    <p className="text-xs mt-3">
                        Only high-confidence contradictions (&gt;70%) are flagged. All flags include
                        evidence links for user verification.
                    </p>
                </div>
            </div>

            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                </div>
            ) : data && data.articles.length === 0 ? (
                <>
                    {/* Source Error Rates (even if no flagged articles, show methodology) */}
                    {data.source_stats && data.source_stats.length > 0 && (
                        <SourceErrorRates sources={data.source_stats} />
                    )}

                    <div className="card bg-green-50 dark:bg-green-900/20 border-l-4 border-green-400">
                        <div className="flex items-start space-x-3">
                            <span className="text-3xl">✅</span>
                            <div>
                                <h3 className="text-xl font-bold text-green-900 dark:text-green-200 mb-2">
                                    No Fact-Check Failures Found
                                </h3>
                                <p className="text-green-800 dark:text-green-300 mb-3">
                                    Great news! Out of {data.summary.total_checked || 0} articles checked in the last 30 days:
                                </p>
                                <ul className="space-y-1 ml-5 list-disc text-green-800 dark:text-green-300">
                                    <li><strong>0 false claims</strong> detected</li>
                                    <li><strong>0 disputed claims</strong> detected</li>
                                    <li>All articles passed verification or contained no checkable claims</li>
                                </ul>
                                <p className="text-sm text-green-700 dark:text-green-400 mt-4">
                                    <strong>This is excellent!</strong> Sources in your database are reporting accurately.
                                    The fact-checker automatically runs every 15 minutes and processes up to 50 new articles per run.
                                </p>
                                <p className="text-xs text-green-600 dark:text-green-500 mt-2 italic">
                                    Note: The system only flags high-confidence contradictions (&gt;70% certainty) to avoid false positives.
                                </p>
                            </div>
                        </div>
                    </div>

                </>
            ) : data ? (
                <>
                    {/* Source Error Rates */}
                    {data.source_stats && data.source_stats.length > 0 && (
                        <SourceErrorRates sources={data.source_stats} />
                    )}

                    {/* Flagged Articles */}
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                            Flagged Articles ({data.total})
                        </h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Showing articles with factual errors, sorted by most recent first
                        </p>
                    </div>

                    <div className="space-y-4">
                        {data.articles.map((article: any) => (
                            <FlaggedArticleCard key={article.id} article={article} />
                        ))}
                    </div>

                    {/* Pagination hint */}
                    {data.total > data.limit && (
                        <div className="card bg-gray-50 dark:bg-gray-900/50 mt-6 text-center">
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Showing {data.articles.length} of {data.total} flagged articles
                            </p>
                        </div>
                    )}
                </>
            ) : null}
        </div>
    );
}

