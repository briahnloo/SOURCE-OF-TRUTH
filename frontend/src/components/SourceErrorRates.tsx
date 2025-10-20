'use client';

import { SourceErrorStats } from '@/lib/api';

interface Props {
    sources: SourceErrorStats[];
}

export default function SourceErrorRates({ sources }: Props) {
    if (sources.length === 0) {
        return null;
    }

    return (
        <div className="card mb-6 border-l-4 border-orange-400 dark:border-orange-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                <span>📊</span>
                <span>Sources with Most Fact-Check Failures</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 font-normal">
                    (Last 30 Days)
                </span>
            </h3>

            <div className="space-y-3">
                {sources.map((source, idx) => (
                    <div
                        key={source.domain}
                        className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                        <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-3">
                                <span className="text-xl font-bold text-gray-400 dark:text-gray-600">
                                    #{idx + 1}
                                </span>
                                <div>
                                    <p className="text-sm font-bold text-gray-900 dark:text-white">
                                        {source.domain}
                                    </p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">
                                        {source.total_articles} articles published
                                    </p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                                    {(source.error_rate * 100).toFixed(1)}%
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">error rate</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-3 mt-3">
                            <div className="text-center p-2 bg-red-100 dark:bg-red-900/30 rounded">
                                <p className="text-lg font-bold text-red-700 dark:text-red-300">
                                    {source.false_count}
                                </p>
                                <p className="text-xs text-red-600 dark:text-red-400">False</p>
                            </div>
                            <div className="text-center p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded">
                                <p className="text-lg font-bold text-yellow-700 dark:text-yellow-300">
                                    {source.disputed_count}
                                </p>
                                <p className="text-xs text-yellow-600 dark:text-yellow-400">
                                    Disputed
                                </p>
                            </div>
                            <div className="text-center p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                <p className="text-lg font-bold text-gray-700 dark:text-gray-300">
                                    {source.flagged_count}
                                </p>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Total Flagged</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-800 dark:text-blue-300">
                <strong>Note:</strong> Error rates are calculated based on the percentage of articles
                from each source that contain verifiably false or disputed claims. This measurement is
                independent of political bias and based solely on factual accuracy.
            </div>
        </div>
    );
}

