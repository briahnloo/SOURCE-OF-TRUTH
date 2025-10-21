'use client';

import { useState } from 'react';

interface NarrativePerspective {
    sources: string[];
    article_count: number;
    representative_title: string;
    key_entities: string[];
    sentiment: string;
    focus_keywords: string[];
    political_leaning?: string;
}

interface ConflictExplanationData {
    perspectives: NarrativePerspective[];
    key_difference: string;
    difference_type: string;
}

interface Props {
    explanation: ConflictExplanationData;
    onExpand?: () => void;
}

export default function QuickCompare({ explanation, onExpand }: Props) {
    const [isExpanded, setIsExpanded] = useState(false);

    const handleToggle = () => {
        if (!isExpanded && onExpand) {
            onExpand();
        }
        setIsExpanded(!isExpanded);
    };

    const getPoliticalLabel = (leaning: string) => {
        switch (leaning) {
            case 'left':
                return 'Liberal sources';
            case 'right':
                return 'Conservative sources';
            case 'center':
                return 'Center sources';
            default:
                return 'Sources';
        }
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
                return '•';
        }
    };

    // Check if we have political grouping
    const hasPoliticalGrouping = explanation.perspectives.some((p) => p.political_leaning);

    if (!hasPoliticalGrouping) {
        return null; // Don't show quick compare if no political grouping
    }

    return (
        <div className="mt-4">
            <button
                onClick={handleToggle}
                className="w-full text-left p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 hover:shadow-md transition-all"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">📊</span>
                        <span className="font-semibold text-gray-900 dark:text-white text-sm">
                            How perspectives differ
                        </span>
                    </div>
                    <span className="text-gray-500 dark:text-gray-400">
                        {isExpanded ? '▼' : '▶'}
                    </span>
                </div>
            </button>

            {isExpanded && (
                <div className="mt-2 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 space-y-3 animate-fade-in">
                    {/* Key Difference Summary */}
                    <div className="pb-3 border-b border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                            <span className="font-semibold">Key difference: </span>
                            {explanation.key_difference}
                        </p>
                    </div>

                    {/* Quick Perspective Summaries */}
                    {explanation.perspectives.map((perspective, idx) => {
                        const firstExcerpt = (perspective as any).representative_excerpts && (perspective as any).representative_excerpts.length > 0
                            ? (perspective as any).representative_excerpts[0]
                            : null;
                        const firstSource = perspective.sources[0];

                        return (
                            <div
                                key={idx}
                                className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50"
                            >
                                <span className="text-xl flex-shrink-0">
                                    {getPoliticalIcon(perspective.political_leaning || '')}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-semibold text-sm text-gray-900 dark:text-white">
                                            {getPoliticalLabel(perspective.political_leaning || '')}
                                        </span>
                                        <span className="text-xs text-gray-500 dark:text-gray-400">
                                            ({perspective.article_count} source{perspective.article_count > 1 ? 's' : ''})
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2">
                                        <span className="font-medium">Focus: </span>
                                        {perspective.focus_keywords.slice(0, 5).map((kw, i) => (
                                            <span key={i}>
                                                &quot;{kw}&quot;
                                                {i < Math.min(4, perspective.focus_keywords.length - 1) ? ', ' : ''}
                                            </span>
                                        ))}
                                    </p>

                                    {/* Show excerpt preview inline */}
                                    {firstExcerpt && (
                                        <div className="mt-2">
                                            <blockquote className="text-xs text-gray-600 dark:text-gray-400 italic border-l-2 border-gray-300 dark:border-gray-600 pl-2 line-clamp-3">
                                                &quot;{firstExcerpt.excerpt}&quot;
                                            </blockquote>
                                            <a
                                                href={firstExcerpt.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1 inline-flex items-center gap-1"
                                            >
                                                <span>Read full article from {firstSource}</span>
                                                <span>↗</span>
                                            </a>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}

                    <div className="pt-2">
                        <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                            💡 Click article links above to read each perspective, or expand detailed comparison below
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

