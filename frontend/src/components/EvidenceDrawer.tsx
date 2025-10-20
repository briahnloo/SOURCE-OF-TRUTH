'use client';

import { useState } from 'react';
import { EventSource, ScoringBreakdown } from '@/lib/api';

interface EvidenceDrawerProps {
    sources: EventSource[];
    scoring?: ScoringBreakdown;
}

export default function EvidenceDrawer({ sources, scoring }: EvidenceDrawerProps) {
    const [isOpen, setIsOpen] = useState(true); // Default to open
    const [showAll, setShowAll] = useState(false);

    const visibleSources = showAll ? sources : sources.slice(0, 3);
    const hasMore = sources.length > 3;

    return (
        <div className="border-t border-gray-200 dark:border-gray-700 mt-4">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between py-4 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors group"
                aria-expanded={isOpen}
            >
                <span className="flex items-center space-x-2">
                    <span className="text-lg">📰</span>
                    <span>Read the Articles ({sources.length} sources)</span>
                </span>
                <svg
                    className={`w-5 h-5 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''
                        }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                    />
                </svg>
            </button>

            {isOpen && (
                <div className="pb-4 space-y-4 animate-fade-in">
                    {/* Scoring breakdown */}
                    {scoring && (
                        <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 rounded-lg p-4 space-y-3 border border-gray-200 dark:border-gray-700">
                            <h4 className="font-semibold text-sm text-gray-900 dark:text-gray-100 flex items-center space-x-2">
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                                </svg>
                                <span>Scoring Breakdown</span>
                            </h4>

                            {Object.entries(scoring).map(([key, component]) => (
                                <div
                                    key={key}
                                    className="flex items-center justify-between text-sm bg-white dark:bg-gray-800 rounded p-2"
                                >
                                    <div className="flex items-center space-x-2">
                                        <span className="text-gray-700 dark:text-gray-300 font-medium">
                                            {key
                                                .split('_')
                                                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                                                .join(' ')}
                                        </span>
                                        <span className="text-xs text-gray-500 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                                            {(component.weight * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <span className="font-bold text-gray-900 dark:text-gray-100 tabular-nums">
                                        {component.value.toFixed(1)} pts
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Sources list */}
                    <div>
                        <h4 className="font-semibold text-sm text-gray-900 dark:text-gray-100 mb-3 flex items-center space-x-2">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                    fillRule="evenodd"
                                    d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <span>All Source Articles</span>
                        </h4>
                        <div className="space-y-2">
                            {visibleSources.map((source, idx) => (
                                <div
                                    key={idx}
                                    className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
                                >
                                    {source.url ? (
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-start justify-between group"
                                        >
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-xs font-semibold text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-2 py-0.5 rounded">
                                                        [{source.domain}]
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-700 dark:text-gray-300 leading-snug group-hover:text-primary-600 dark:group-hover:text-primary-400">
                                                    {source.title}
                                                </p>
                                            </div>
                                            <svg
                                                className="w-5 h-5 ml-3 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors flex-shrink-0"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                                />
                                            </svg>
                                        </a>
                                    ) : (
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-xs font-semibold text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-2 py-0.5 rounded">
                                                        [{source.domain}]
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-700 dark:text-gray-300 leading-snug">
                                                    {source.title}
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {hasMore && !showAll && (
                            <button
                                onClick={() => setShowAll(true)}
                                className="mt-3 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                            >
                                Show all {sources.length} sources →
                            </button>
                        )}

                        {showAll && hasMore && (
                            <button
                                onClick={() => setShowAll(false)}
                                className="mt-3 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                            >
                                Show less
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
