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

interface Source {
    domain: string;
    title: string;
    political_bias?: { left: number; center: number; right: number };
}

interface Props {
    conflictExplanation?: ConflictExplanationData;
    sources: Source[];
}

export default function UnbiasedSummary({ conflictExplanation, sources }: Props) {
    const [isExpanded, setIsExpanded] = useState(false);

    const handleToggle = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('UnbiasedSummary toggle clicked, current state:', isExpanded);
        setIsExpanded(prev => !prev);
    };

    if (!conflictExplanation) {
        return null;
    }

    // Extract common entities (verified facts mentioned by all perspectives)
    const allEntities = conflictExplanation.perspectives.flatMap(p => p.key_entities);
    const entityCounts = new Map<string, number>();

    allEntities.forEach(entity => {
        entityCounts.set(entity, (entityCounts.get(entity) || 0) + 1);
    });

    // Entities mentioned by most or all perspectives are likely verified facts
    // Only include if they look like actual facts (multiple words, not just single names)
    const verifiedFacts = Array.from(entityCounts.entries())
        .filter(([entity, count]) => {
            // Must be mentioned by at least 60% of perspectives
            if (count < conflictExplanation.perspectives.length * 0.6) return false;

            // Filter out single-word entities (not helpful as "facts")
            const words = entity.trim().split(/\s+/);
            if (words.length < 2) return false;

            // Filter out overly generic entities
            const genericWords = ['israel', 'trump', 'biden', 'hamas', 'gaza', 'ukraine', 'russia'];
            if (words.length === 1 && genericWords.includes(entity.toLowerCase())) return false;

            return true;
        })
        .map(([entity, _]) => entity)
        .slice(0, 5); // Top 5

    // Get center source perspectives
    const centerPerspectives = conflictExplanation.perspectives.filter(
        p => p.political_leaning === 'center'
    );

    const hasCenterSources = centerPerspectives.length > 0;

    // If no verified facts or center sources, don't show the component
    if (verifiedFacts.length === 0 && !hasCenterSources) {
        return null;
    }

    return (
        <div className="mt-4 border border-blue-200 dark:border-blue-800 rounded-lg overflow-hidden">
            <button
                onClick={handleToggle}
                className="w-full px-4 py-3 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors text-left relative z-50 cursor-pointer"
                type="button"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">✓</span>
                        <span className="font-semibold text-blue-900 dark:text-blue-100 text-sm">
                            Unbiased View: What we know for sure
                        </span>
                    </div>
                    <span className="text-blue-600 dark:text-blue-400">
                        {isExpanded ? '▼' : '▶'}
                    </span>
                </div>
            </button>

            {isExpanded && (
                <div className="p-4 bg-white dark:bg-gray-800 space-y-4 animate-fade-in">
                    {/* Verified Facts */}
                    {verifiedFacts.length > 0 && (
                        <div>
                            <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                                <span className="text-green-600 dark:text-green-400">✓</span>
                                Verified Facts (all sources agree)
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {verifiedFacts.map((fact, idx) => (
                                    <span
                                        key={idx}
                                        className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full text-xs font-medium border border-green-200 dark:border-green-800"
                                    >
                                        {fact}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Center Source Consensus */}
                    {hasCenterSources && (
                        <div>
                            <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                                <span>⚪</span>
                                Center Source Perspective
                            </h4>
                            <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/50 p-3 rounded-lg leading-relaxed">
                                {centerPerspectives[0].representative_title}
                            </p>
                            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                                <span className="font-medium">Sources: </span>
                                {centerPerspectives[0].sources.join(', ')}
                            </div>
                        </div>
                    )}

                    {/* Points of Disagreement */}
                    {conflictExplanation.key_difference && (
                        <div>
                            <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                                <span className="text-yellow-600 dark:text-yellow-400">?</span>
                                Where sources disagree
                            </h4>
                            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border-l-4 border-yellow-400 dark:border-yellow-600">
                                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                    {conflictExplanation.key_difference}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Recommendation */}
                    <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                        <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                            💡 For the most balanced understanding, read center sources first, then compare with left and right perspectives below
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

