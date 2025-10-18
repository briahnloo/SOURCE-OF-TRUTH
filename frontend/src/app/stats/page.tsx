import { api } from '@/lib/api';
import StatsPanel from '@/components/StatsPanel';

export const revalidate = 60;

export default async function StatsPage() {
    let stats: any = null;
    let error: string | null = null;

    try {
        stats = await api.getStats();
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch stats';
        console.error('Error fetching stats:', e);
    }

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    System Statistics
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                    Real-time metrics from the Truth Layer verification engine
                </p>
            </div>

            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                </div>
            ) : stats ? (
                <>
                    <StatsPanel stats={stats} />

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
                        {/* Top Sources */}
                        <div className="card">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center space-x-2">
                                <span className="text-2xl">🏆</span>
                                <span>Top Sources</span>
                            </h2>
                            <div className="space-y-3">
                                {stats.top_sources.slice(0, 10).map((source: any, idx: number) => (
                                    <div
                                        key={source.domain}
                                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                    >
                                        <div className="flex items-center space-x-3">
                                            <span className="flex items-center justify-center w-8 h-8 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 font-bold rounded-full text-sm">
                                                {idx + 1}
                                            </span>
                                            <span className="font-medium text-gray-900 dark:text-white">
                                                {source.domain}
                                            </span>
                                        </div>
                                        <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 tabular-nums">
                                            {source.article_count.toLocaleString()} articles
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Coverage Breakdown */}
                        <div className="card">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center space-x-2">
                                <span className="text-2xl">📈</span>
                                <span>Coverage Distribution</span>
                            </h2>
                            <div className="space-y-6">
                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="w-3 h-3 bg-confirmed rounded-full"></span>
                                            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                                Confirmed (≥75)
                                            </span>
                                        </div>
                                        <span className="text-lg font-bold text-confirmed-dark tabular-nums">
                                            {stats.coverage_by_tier.confirmed}
                                        </span>
                                    </div>
                                    <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                                        <div
                                            className="gradient-confirmed h-3 rounded-full transition-all duration-1000"
                                            style={{
                                                width: `${stats.total_events > 0
                                                        ? (stats.coverage_by_tier.confirmed / stats.total_events) * 100
                                                        : 0
                                                    }%`,
                                            }}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="w-3 h-3 bg-developing rounded-full"></span>
                                            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                                Developing (40-74)
                                            </span>
                                        </div>
                                        <span className="text-lg font-bold text-developing-dark tabular-nums">
                                            {stats.coverage_by_tier.developing}
                                        </span>
                                    </div>
                                    <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                                        <div
                                            className="gradient-developing h-3 rounded-full transition-all duration-1000"
                                            style={{
                                                width: `${stats.total_events > 0
                                                        ? (stats.coverage_by_tier.developing / stats.total_events) * 100
                                                        : 0
                                                    }%`,
                                            }}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="w-3 h-3 bg-gray-400 rounded-full"></span>
                                            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                                Unverified (&lt;40)
                                            </span>
                                        </div>
                                        <span className="text-lg font-bold text-gray-600 dark:text-gray-400 tabular-nums">
                                            {stats.coverage_by_tier.unverified}
                                        </span>
                                    </div>
                                    <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                                        <div
                                            className="bg-gray-400 h-3 rounded-full transition-all duration-1000"
                                            style={{
                                                width: `${stats.total_events > 0
                                                        ? (stats.coverage_by_tier.unverified / stats.total_events) * 100
                                                        : 0
                                                    }%`,
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className="card">
                    <p className="text-gray-600 dark:text-gray-400 text-center py-8">
                        Loading statistics...
                    </p>
                </div>
            )}
        </div>
    );
}
