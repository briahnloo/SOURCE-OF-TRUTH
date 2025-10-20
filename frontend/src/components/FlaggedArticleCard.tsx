'use client';

import { FlaggedArticle } from '@/lib/api';

interface Props {
    article: FlaggedArticle;
}

export default function FlaggedArticleCard({ article }: Props) {
    const getStatusColor = (status: string) => {
        if (status === 'false')
            return 'bg-red-50 border-red-500 dark:bg-red-900/20 dark:border-red-700';
        if (status === 'disputed')
            return 'bg-yellow-50 border-yellow-500 dark:bg-yellow-900/20 dark:border-yellow-700';
        return 'bg-orange-50 border-orange-500 dark:bg-orange-900/20 dark:border-orange-700';
    };

    const getStatusIcon = (status: string) => {
        if (status === 'false') return '❌';
        if (status === 'disputed') return '⚠️';
        return '❓';
    };

    const getVerdictColor = (verdict: string) => {
        if (verdict === 'false') return 'text-red-700 dark:text-red-300 font-bold';
        if (verdict === 'disputed' || verdict === 'misleading')
            return 'text-yellow-700 dark:text-yellow-300 font-semibold';
        return 'text-orange-700 dark:text-orange-300';
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className={`border-l-4 rounded-lg p-5 ${getStatusColor(article.fact_check_status)}`}>
            <div className="flex items-start space-x-3">
                <span className="text-3xl flex-shrink-0">{getStatusIcon(article.fact_check_status)}</span>

                <div className="flex-1">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                        <div>
                            <span className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide block mb-1">
                                {article.source}
                            </span>
                            <span
                                className={`text-xs px-2.5 py-1 rounded font-bold ${article.fact_check_status === 'false'
                                    ? 'bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-200'
                                    : 'bg-yellow-200 text-yellow-900 dark:bg-yellow-800 dark:text-yellow-200'
                                    }`}
                            >
                                {article.fact_check_status?.toUpperCase()}
                            </span>
                        </div>
                        <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                        >
                            View article ↗
                        </a>
                    </div>

                    {/* Article Title */}
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                        &quot;{article.title}&quot;
                    </h3>

                    {/* Timestamp */}
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                        Published: {formatDate(article.timestamp)}
                    </p>

                    {/* Fact-Check Flags */}
                    {article.fact_check_flags && article.fact_check_flags.length > 0 && (
                        <div className="space-y-3">
                            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Factual Issues Identified ({article.fact_check_flags.length}):
                            </p>
                            {article.fact_check_flags.map((flag, idx) => (
                                <div
                                    key={idx}
                                    className="p-4 bg-white dark:bg-gray-800 rounded-lg border-2 border-gray-200 dark:border-gray-700"
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <span
                                            className={`text-sm font-bold ${getVerdictColor(flag.verdict)} uppercase tracking-wide`}
                                        >
                                            {flag.verdict}
                                        </span>
                                        <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                            {(flag.confidence * 100).toFixed(0)}% confidence
                                        </span>
                                    </div>

                                    <div className="space-y-3">
                                        {/* Claim Location Badge */}
                                        {flag.claim_location && (
                                            <div className="flex items-center space-x-2 mb-2">
                                                <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded font-medium">
                                                    Found in: {flag.claim_location}
                                                </span>
                                            </div>
                                        )}

                                        <div>
                                            <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1 uppercase tracking-wide">
                                                CLAIM:
                                            </p>
                                            <p className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                                                &quot;{flag.claim}&quot;
                                            </p>
                                        </div>

                                        {/* Claim Context */}
                                        {flag.claim_context && flag.claim_context !== flag.claim && (
                                            <div className="p-2 bg-gray-100 dark:bg-gray-700/50 rounded text-xs">
                                                <p className="font-semibold text-gray-600 dark:text-gray-400 mb-1">
                                                    Context from article:
                                                </p>
                                                <p className="text-gray-700 dark:text-gray-300 italic">
                                                    ...{flag.claim_context}...
                                                </p>
                                            </div>
                                        )}

                                        <div>
                                            <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1 uppercase tracking-wide">
                                                WHY IT&apos;S WRONG:
                                            </p>
                                            <p className="text-sm text-gray-800 dark:text-gray-200">
                                                {flag.explanation}
                                            </p>
                                        </div>

                                        <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                                                        <strong>Verified by:</strong>
                                                    </p>
                                                    <p className="text-sm text-gray-800 dark:text-gray-200 font-medium">
                                                        {flag.evidence_source}
                                                    </p>
                                                </div>
                                                {flag.evidence_url && (
                                                    <a
                                                        href={flag.evidence_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                                    >
                                                        See evidence ↗
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

