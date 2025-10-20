'use client';

interface FactCheckFlag {
    claim: string;
    verdict: string;
    evidence_source: string;
    evidence_url?: string;
    explanation: string;
    confidence: number;
}

interface Article {
    id: number;
    source: string;
    title: string;
    url: string;
    fact_check_status?: string;
    fact_check_flags?: FactCheckFlag[];
}

interface Props {
    articles: Article[];
}

export default function FactCheckWarnings({ articles }: Props) {
    const flaggedArticles = articles.filter(
        (a) =>
            a.fact_check_status &&
            a.fact_check_status !== 'verified' &&
            a.fact_check_status !== 'unverified'
    );

    if (flaggedArticles.length === 0) {
        return null;
    }

    const getStatusColor = (status: string) => {
        if (status === 'false')
            return 'bg-red-50 border-red-400 dark:bg-red-900/20 dark:border-red-800';
        if (status === 'disputed')
            return 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-800';
        return 'bg-orange-50 border-orange-400 dark:bg-orange-900/20 dark:border-orange-800';
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

    return (
        <div className="card mt-4 border-l-4 border-red-400 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10">
            <div className="space-y-3">
                <div className="flex items-center space-x-2">
                    <h4 className="text-md font-semibold text-gray-900 dark:text-white">
                        🔍 Fact-Check Warnings
                    </h4>
                    <span className="text-xs bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 px-2 py-0.5 rounded font-semibold">
                        {flaggedArticles.length}{' '}
                        {flaggedArticles.length === 1 ? 'source' : 'sources'}
                    </span>
                </div>

                <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                    The following sources contain claims that contradict official data or have been
                    fact-checked as inaccurate:
                </p>

                <div className="space-y-3">
                    {flaggedArticles.map((article) => (
                        <div
                            key={article.id}
                            className={`p-4 border-l-4 rounded-lg ${getStatusColor(article.fact_check_status!)}`}
                        >
                            <div className="flex items-start space-x-2">
                                <span className="text-xl">{getStatusIcon(article.fact_check_status!)}</span>
                                <div className="flex-1">
                                    <div className="flex items-start justify-between mb-2">
                                        <div>
                                            <span className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                                {article.source}
                                            </span>
                                            <span
                                                className={`ml-2 text-xs px-2 py-0.5 rounded font-bold ${article.fact_check_status === 'false'
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
                                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                        >
                                            View article ↗
                                        </a>
                                    </div>

                                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3">
                                        &quot;{article.title}&quot;
                                    </p>

                                    {article.fact_check_flags &&
                                        article.fact_check_flags.length > 0 && (
                                            <div className="space-y-2">
                                                <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                                    Factual Issues Identified:
                                                </p>
                                                {article.fact_check_flags.map((flag, idx) => (
                                                    <div
                                                        key={idx}
                                                        className="p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                                                    >
                                                        <div className="flex items-start justify-between mb-2">
                                                            <span
                                                                className={`text-xs font-bold ${getVerdictColor(flag.verdict)} uppercase tracking-wide`}
                                                            >
                                                                {flag.verdict}
                                                            </span>
                                                            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                                                {(flag.confidence * 100).toFixed(0)}%
                                                                confidence
                                                            </span>
                                                        </div>

                                                        <div className="space-y-2">
                                                            <div>
                                                                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">
                                                                    CLAIM:
                                                                </p>
                                                                <p className="text-sm text-gray-800 dark:text-gray-200">
                                                                    &quot;{flag.claim}&quot;
                                                                </p>
                                                            </div>

                                                            <div>
                                                                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">
                                                                    WHY IT&apos;S WRONG:
                                                                </p>
                                                                <p className="text-sm text-gray-700 dark:text-gray-300">
                                                                    {flag.explanation}
                                                                </p>
                                                            </div>

                                                            <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
                                                                <span className="text-xs text-gray-600 dark:text-gray-400">
                                                                    <strong>Verified by:</strong>{' '}
                                                                    {flag.evidence_source}
                                                                </span>
                                                                {flag.evidence_url && (
                                                                    <a
                                                                        href={flag.evidence_url}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                                                    >
                                                                        See evidence ↗
                                                                    </a>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-800 dark:text-blue-300">
                    <strong>How we fact-check:</strong> We verify claims against (1) Google Fact
                    Check API (aggregates PolitiFact, Snopes, FactCheck.org), (2) Official
                    government sources (USGS, WHO, NASA), and (3) Cross-referencing with multiple
                    verified sources. Only high-confidence contradictions (&gt;70%) are flagged.
                </div>
            </div>
        </div>
    );
}

