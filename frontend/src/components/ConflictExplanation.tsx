'use client';

import { useState } from 'react';

interface ArticleExcerpt {
    source: string;
    title: string;
    url: string;
    excerpt: string;
    relevance_score: number;
}

interface NarrativePerspective {
    sources: string[];
    article_count: number;
    representative_title: string;
    key_entities: string[];
    sentiment: string;
    focus_keywords: string[];
    political_leaning?: string;
    representative_excerpts?: ArticleExcerpt[];
}

interface NumericDiscrepancy {
    metric: string;
    values_by_perspective: {
        [key: string]: {
            value: string;
            leaning: string;
            leaning_label: string;
        };
    };
    significance: string;
}

interface ConflictExplanationData {
    perspectives: NarrativePerspective[];
    key_difference: string;
    difference_type: string;
    numeric_discrepancies?: NumericDiscrepancy[];
}

interface Props {
    explanation: ConflictExplanationData;
    severity: string;
}

export default function ConflictExplanation({ explanation, severity }: Props) {
    const [expandedPerspectives, setExpandedPerspectives] = useState<Set<number>>(new Set());
    const [isMainExpanded, setIsMainExpanded] = useState(true); // Default to expanded

    const toggleMain = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('ConflictExplanation main toggle clicked, current state:', isMainExpanded);
        setIsMainExpanded(prev => !prev);
    };

    const toggleExpanded = (index: number, e?: React.MouseEvent) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        const newExpanded = new Set(expandedPerspectives);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedPerspectives(newExpanded);
    };

    const getIcon = () => {
        switch (explanation.difference_type) {
            case 'facts':
                return '📊';
            case 'emphasis':
                return '🎯';
            case 'framing':
                return '🖼️';
            case 'interpretation':
                return '💭';
            default:
                return '🔍';
        }
    };

    const getSentimentColor = (sentiment: string) => {
        switch (sentiment) {
            case 'positive':
                return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
            case 'negative':
                return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
            default:
                return 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
        }
    };

    const getBorderColor = (idx: number) => {
        const colors = [
            'border-blue-400 dark:border-blue-600',
            'border-purple-400 dark:border-purple-600',
            'border-orange-400 dark:border-orange-600',
        ];
        return colors[idx % colors.length];
    };

    const getPoliticalLabel = (leaning: string) => {
        switch (leaning) {
            case 'left':
                return 'Liberal Sources';
            case 'right':
                return 'Conservative Sources';
            case 'center':
                return 'Center Sources';
            default:
                return 'Sources';
        }
    };

    const isInternationalPerspective = (perspective: NarrativePerspective) => {
        // Check if sources are international (non-US domains)
        const internationalDomains = [
            'bbc.co.uk', 'feeds.bbci.co.uk', 'aljazeera.com', 'dw.com', 'rss.dw.com',
            'france24.com', 'nhk.or.jp', 'www3.nhk.or.jp', 'abc.net.au', 'cbc.ca',
            'euronews.com', 'africanews.com', 'straitstimes.com'
        ];

        return perspective.sources.some(source =>
            internationalDomains.some(domain => source.includes(domain))
        );
    };

    const getPoliticalIcon = (leaning: string) => {
        switch (leaning) {
            case 'left':
                return '🔵';
            case 'right':
                return '🔴';
            case 'center':
                return '⚪';
            default:
                return '';
        }
    };

    const getPoliticalBorderColor = (leaning: string) => {
        switch (leaning) {
            case 'left':
                return 'border-blue-500 dark:border-blue-400';
            case 'right':
                return 'border-red-500 dark:border-red-400';
            case 'center':
                return 'border-gray-400 dark:border-gray-500';
            default:
                return 'border-gray-400 dark:border-gray-600';
        }
    };

    const getPoliticalBgColor = (leaning: string) => {
        switch (leaning) {
            case 'left':
                return 'bg-blue-50 dark:bg-blue-900/10';
            case 'right':
                return 'bg-red-50 dark:bg-red-900/10';
            case 'center':
                return 'bg-gray-50 dark:bg-gray-900/50';
            default:
                return 'bg-gray-50 dark:bg-gray-900/50';
        }
    };

    // Check if we have political grouping
    const hasPoliticalGrouping = explanation.perspectives.some((p) => p.political_leaning);

    return (
        <div className="mt-4">
            <button
                onClick={toggleMain}
                className="w-full text-left px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 hover:from-blue-100 hover:to-purple-100 dark:hover:from-blue-900/30 dark:hover:to-purple-900/30 transition-colors rounded-lg border border-blue-200 dark:border-blue-800 relative z-50 cursor-pointer"
                type="button"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">{getIcon()}</span>
                        <span className="font-semibold text-gray-900 dark:text-white text-base">
                            {hasPoliticalGrouping
                                ? 'Left vs Right Coverage'
                                : 'Perspective Breakdown'}
                        </span>
                    </div>
                    <span className="text-gray-500 dark:text-gray-400">
                        {isMainExpanded ? '▼' : '▶'}
                    </span>
                </div>
            </button>

            {isMainExpanded && (
                <div className="mt-2 p-5 bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 shadow-sm animate-fade-in">
                    {/* Key difference summary - Enhanced UI */}
                    <div className="mb-5 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border-l-4 border-blue-500 dark:border-blue-400 shadow-sm">
                        <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0 mt-0.5">
                                <span className="text-xl">💡</span>
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wide mb-2">
                                    Why this is flagged as conflicting
                                </div>
                                <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-medium">
                                    {explanation.key_difference}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Numerical Discrepancies Section */}
                    {explanation.numeric_discrepancies &&
                        explanation.numeric_discrepancies.length > 0 && (
                            <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border-l-4 border-yellow-500">
                                <div className="flex items-start space-x-2">
                                    <span className="text-xl">📊</span>
                                    <div className="flex-1">
                                        <h5 className="font-bold text-sm text-gray-900 dark:text-white mb-2">
                                            Numerical Discrepancies Detected
                                        </h5>
                                        {explanation.numeric_discrepancies.map((discrepancy, idx) => (
                                            <div
                                                key={idx}
                                                className={`mb-3 ${idx > 0 ? 'mt-3 pt-3 border-t border-yellow-200 dark:border-yellow-800' : ''
                                                    }`}
                                            >
                                                <div className="text-xs font-semibold text-gray-900 dark:text-white mb-1">
                                                    {discrepancy.metric}:
                                                </div>
                                                <div className="space-y-1">
                                                    {Object.entries(discrepancy.values_by_perspective).map(
                                                        ([perspectiveIdx, data]) => {
                                                            const perspective =
                                                                explanation.perspectives[
                                                                parseInt(perspectiveIdx)
                                                                ];
                                                            const leaningColor =
                                                                data.leaning === 'left'
                                                                    ? 'text-blue-700 dark:text-blue-400'
                                                                    : data.leaning === 'right'
                                                                        ? 'text-red-700 dark:text-red-400'
                                                                        : 'text-gray-700 dark:text-gray-400';
                                                            const leaningIcon =
                                                                data.leaning === 'left'
                                                                    ? '🔵'
                                                                    : data.leaning === 'right'
                                                                        ? '🔴'
                                                                        : '⚪';

                                                            return (
                                                                <div
                                                                    key={perspectiveIdx}
                                                                    className="text-xs flex items-center gap-2"
                                                                >
                                                                    <span>{leaningIcon}</span>
                                                                    <span
                                                                        className={`font-semibold ${leaningColor}`}
                                                                    >
                                                                        {data.leaning_label}:
                                                                    </span>
                                                                    <span className="font-bold text-gray-900 dark:text-white">
                                                                        {data.value}
                                                                    </span>
                                                                </div>
                                                            );
                                                        }
                                                    )}
                                                </div>
                                                {discrepancy.significance === 'high' && (
                                                    <div className="mt-1 text-xs text-red-700 dark:text-red-400 font-semibold">
                                                        ⚠️ Major discrepancy (10x+ difference)
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                        <p className="text-xs text-yellow-800 dark:text-yellow-300 mt-2">
                                            💡 These numbers differ significantly between sources. This could
                                            indicate different methodologies, time periods, or intentional
                                            framing differences.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                    <div className="space-y-4 mt-5">
                        {explanation.perspectives.map((perspective, idx) => (
                            <div
                                key={idx}
                                className={`p-4 rounded-lg border-l-4 transition-all duration-200 hover:shadow-md ${hasPoliticalGrouping && perspective.political_leaning
                                    ? `${getPoliticalBgColor(perspective.political_leaning)} ${getPoliticalBorderColor(perspective.political_leaning)}`
                                    : `bg-gray-50 dark:bg-gray-900/50 ${getBorderColor(idx)}`
                                    }`}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    {hasPoliticalGrouping && perspective.political_leaning ? (
                                        <div className="flex items-center space-x-3">
                                            <span className="text-2xl">
                                                {getPoliticalIcon(perspective.political_leaning)}
                                            </span>
                                            <div>
                                                <span className="text-base font-bold text-gray-900 dark:text-white block">
                                                    {getPoliticalLabel(perspective.political_leaning)}
                                                </span>
                                                <span className="text-xs text-gray-600 dark:text-gray-400">
                                                    {perspective.article_count} source
                                                    {perspective.article_count > 1 ? 's' : ''}
                                                </span>
                                            </div>
                                        </div>
                                    ) : isInternationalPerspective(perspective) ? (
                                        <div className="flex items-center space-x-3">
                                            <span className="text-2xl">🌍</span>
                                            <div>
                                                <span className="text-base font-bold text-gray-900 dark:text-white block">
                                                    International Sources
                                                </span>
                                                <span className="text-xs text-gray-600 dark:text-gray-400">
                                                    {perspective.article_count} source
                                                    {perspective.article_count > 1 ? 's' : ''}
                                                </span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div>
                                            <span className="text-sm font-bold text-gray-900 dark:text-white block uppercase">
                                                Perspective {String.fromCharCode(65 + idx)}
                                            </span>
                                            <span className="text-xs text-gray-600 dark:text-gray-400">
                                                {perspective.article_count} source
                                                {perspective.article_count > 1 ? 's' : ''}
                                            </span>
                                        </div>
                                    )}
                                    {!hasPoliticalGrouping && (
                                        <span
                                            className={`text-xs px-2 py-0.5 rounded ${getSentimentColor(perspective.sentiment)}`}
                                        >
                                            {perspective.sentiment}
                                        </span>
                                    )}
                                </div>

                                {perspective.representative_excerpts && perspective.representative_excerpts.length > 0 ? (
                                    <a
                                        href={perspective.representative_excerpts[0].url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline mb-3 leading-relaxed block"
                                    >
                                        &quot;{perspective.representative_title}&quot; →
                                    </a>
                                ) : (
                                    <p className="text-sm font-semibold text-gray-900 dark:text-white mb-3 leading-relaxed">
                                        &quot;{perspective.representative_title}&quot;
                                    </p>
                                )}

                                <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                    <div>
                                        <strong>Sources:</strong>{' '}
                                        {(() => {
                                            // Deduplicate sources and show counts
                                            const sourceCounts = new Map<string, number>();
                                            perspective.sources.forEach(s => {
                                                sourceCounts.set(s, (sourceCounts.get(s) || 0) + 1);
                                            });
                                            return Array.from(sourceCounts.entries())
                                                .map(([source, count]) =>
                                                    count > 1 ? `${source} (${count} articles)` : source
                                                )
                                                .join(', ');
                                        })()}
                                    </div>
                                    {perspective.focus_keywords.length > 0 && (
                                        <div>
                                            <strong>Focus:</strong>{' '}
                                            {perspective.focus_keywords.slice(0, 5).join(', ')}
                                        </div>
                                    )}
                                </div>

                                {/* Article excerpts or fallback */}
                                <div className="mt-3">
                                    {perspective.representative_excerpts && perspective.representative_excerpts.length > 0 ? (
                                        <div className="space-y-3">
                                            <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                                Key articles showing this perspective:
                                            </div>

                                            {/* Always show first 2 excerpts (skip useless ones) */}
                                            {perspective.representative_excerpts
                                                .filter(excerpt => {
                                                    // Filter out useless USGS excerpts
                                                    const uselessPhrases = [
                                                        'supports most recent browsers',
                                                        'view supported browsers',
                                                        'Real-time Notifications, Feeds, and Web Services'
                                                    ];
                                                    return !uselessPhrases.some(phrase =>
                                                        excerpt.excerpt.includes(phrase)
                                                    );
                                                })
                                                .slice(0, 2)
                                                .map((excerpt, excerptIdx) => (
                                                    <div
                                                        key={excerptIdx}
                                                        className={`p-2 rounded-md border-l-2 ${hasPoliticalGrouping &&
                                                            perspective.political_leaning
                                                            ? getPoliticalBorderColor(
                                                                perspective.political_leaning
                                                            )
                                                            : 'border-gray-300 dark:border-gray-600'
                                                            } bg-white dark:bg-gray-800`}
                                                    >
                                                        <div className="mb-2">
                                                            <a
                                                                href={excerpt.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2"
                                                            >
                                                                <span>[{excerpt.source}]</span>
                                                                <span className="text-gray-700 dark:text-gray-300">{excerpt.title}</span>
                                                            </a>
                                                        </div>
                                                        <blockquote className="text-sm text-gray-800 dark:text-gray-200 italic leading-relaxed pl-3 border-l-2 border-gray-300 dark:border-gray-600 mb-2">
                                                            &quot;{excerpt.excerpt}&quot;
                                                        </blockquote>
                                                        <a
                                                            href={excerpt.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                                        >
                                                            Read full article →
                                                        </a>
                                                        {excerpt.relevance_score >= 0.8 && (
                                                            <div className="mt-2 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                                                <span>✓</span>
                                                                <span>
                                                                    Highly relevant to perspective
                                                                    differences
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )
                                                )}

                                            {/* Show button for additional excerpts if more than 2 exist */}
                                            {(() => {
                                                const filteredExcerpts = perspective.representative_excerpts.filter(excerpt => {
                                                    const uselessPhrases = [
                                                        'supports most recent browsers',
                                                        'view supported browsers',
                                                        'Real-time Notifications, Feeds, and Web Services'
                                                    ];
                                                    return !uselessPhrases.some(phrase => excerpt.excerpt.includes(phrase));
                                                });
                                                const remainingCount = filteredExcerpts.length - 2;

                                                return remainingCount > 0 && (
                                                    <>
                                                        <button
                                                            onClick={(e) => toggleExpanded(idx, e)}
                                                            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors flex items-center gap-1 relative z-50 cursor-pointer"
                                                            type="button"
                                                        >
                                                            {expandedPerspectives.has(idx) ? (
                                                                <>
                                                                    <span>▼</span>
                                                                    <span>See less</span>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <span>▶</span>
                                                                    <span>See {remainingCount} more excerpt{remainingCount > 1 ? 's' : ''}</span>
                                                                </>
                                                            )}
                                                        </button>

                                                        {/* Additional excerpts (3+) */}
                                                        {expandedPerspectives.has(idx) && (
                                                            <div className="space-y-3 animate-fade-in">
                                                                {perspective.representative_excerpts
                                                                    .slice(2)
                                                                    .filter(excerpt => {
                                                                        // Filter out useless USGS excerpts
                                                                        const uselessPhrases = [
                                                                            'supports most recent browsers',
                                                                            'view supported browsers',
                                                                            'Real-time Notifications, Feeds, and Web Services'
                                                                        ];
                                                                        return !uselessPhrases.some(phrase =>
                                                                            excerpt.excerpt.includes(phrase)
                                                                        );
                                                                    })
                                                                    .map((excerpt, excerptIdx) => (
                                                                        <div
                                                                            key={excerptIdx + 2}
                                                                            className={`p-2 rounded-md border-l-2 ${hasPoliticalGrouping &&
                                                                                perspective.political_leaning
                                                                                ? getPoliticalBorderColor(
                                                                                    perspective.political_leaning
                                                                                )
                                                                                : 'border-gray-300 dark:border-gray-600'
                                                                                } bg-white dark:bg-gray-800`}
                                                                        >
                                                                            <div className="mb-2">
                                                                                <a
                                                                                    href={excerpt.url}
                                                                                    target="_blank"
                                                                                    rel="noopener noreferrer"
                                                                                    className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2"
                                                                                >
                                                                                    <span>[{excerpt.source}]</span>
                                                                                    <span className="text-gray-700 dark:text-gray-300">{excerpt.title}</span>
                                                                                </a>
                                                                            </div>
                                                                            <blockquote className="text-sm text-gray-800 dark:text-gray-200 italic leading-relaxed pl-3 border-l-2 border-gray-300 dark:border-gray-600 mb-2">
                                                                                &quot;{excerpt.excerpt}&quot;
                                                                            </blockquote>
                                                                            <a
                                                                                href={excerpt.url}
                                                                                target="_blank"
                                                                                rel="noopener noreferrer"
                                                                                className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                                                            >
                                                                                Read full article →
                                                                            </a>
                                                                            {excerpt.relevance_score >= 0.8 && (
                                                                                <div className="mt-2 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                                                                    <span>✓</span>
                                                                                    <span>
                                                                                        Highly relevant to perspective
                                                                                        differences
                                                                                    </span>
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    )
                                                                    )}
                                                            </div>
                                                        )}
                                                    </>
                                                );
                                            })()}
                                        </div>
                                    ) : (
                                        // Clean fallback when no excerpts are available - just show article links
                                        <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 italic">
                                            📰 Read full articles to compare this perspective (see &quot;Read the Articles&quot; section below)
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

