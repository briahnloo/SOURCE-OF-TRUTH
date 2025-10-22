'use client';

import { PolarizingSource } from '@/lib/api';
import { useState } from 'react';

interface PolarizingSourceCardProps {
    source: PolarizingSource;
    rank: number;
}

export default function PolarizingSourceCard({ source, rank }: PolarizingSourceCardProps) {
    const [showExcerpts, setShowExcerpts] = useState(false);

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    // Color scale for polarization score
    const getScoreColor = (score: number) => {
        if (score >= 70) return 'bg-red-500';
        if (score >= 50) return 'bg-orange-500';
        if (score >= 30) return 'bg-yellow-500';
        return 'bg-green-500';
    };

    const getScoreTextColor = (score: number) => {
        if (score >= 70) return 'text-red-700 dark:text-red-400';
        if (score >= 50) return 'text-orange-700 dark:text-orange-400';
        if (score >= 30) return 'text-yellow-700 dark:text-yellow-400';
        return 'text-green-700 dark:text-green-400';
    };

    // Political leaning label
    const getPoliticalLeaning = () => {
        const { left, center, right } = source.political_bias;
        if (left > center && left > right) return 'Left-leaning';
        if (right > center && right > left) return 'Right-leaning';
        return 'Center';
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all duration-300">
            <div className="p-6">
                {/* Header with rank and domain */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-primary-600 to-primary-800 rounded-xl flex items-center justify-center shadow-md">
                            <span className="text-white font-bold text-xl">#{rank}</span>
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                                {source.domain}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                {source.article_count} articles analyzed
                            </p>
                        </div>
                    </div>
                </div>

                {/* Polarization Score */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                            Polarization Score
                        </span>
                        <span className={`text-2xl font-bold ${getScoreTextColor(source.polarization_score)}`}>
                            {source.polarization_score.toFixed(1)}
                        </span>
                    </div>
                    {/* Score bar */}
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div
                            className={`h-full ${getScoreColor(source.polarization_score)} transition-all duration-500`}
                            style={{ width: `${source.polarization_score}%` }}
                        />
                    </div>
                </div>

                {/* Bias Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    {/* Political Bias */}
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            Political Bias
                        </h4>
                        <div className="space-y-2">
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-600 dark:text-gray-400">Left</span>
                                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                                        {(source.political_bias.left * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div
                                        className="bg-blue-500 h-2 rounded-full transition-all"
                                        style={{ width: `${source.political_bias.left * 100}%` }}
                                    />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-600 dark:text-gray-400">Center</span>
                                    <span className="font-semibold text-purple-600 dark:text-purple-400">
                                        {(source.political_bias.center * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div
                                        className="bg-purple-500 h-2 rounded-full transition-all"
                                        style={{ width: `${source.political_bias.center * 100}%` }}
                                    />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-600 dark:text-gray-400">Right</span>
                                    <span className="font-semibold text-red-600 dark:text-red-400">
                                        {(source.political_bias.right * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div
                                        className="bg-red-500 h-2 rounded-full transition-all"
                                        style={{ width: `${source.political_bias.right * 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 font-semibold">
                            {getPoliticalLeaning()}
                        </p>
                    </div>

                    {/* Tone Bias */}
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            Tone Analysis
                        </h4>
                        <div className="space-y-2">
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-600 dark:text-gray-400">Sensational</span>
                                    <span className="font-semibold text-orange-600 dark:text-orange-400">
                                        {(source.tone_bias.sensational * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div
                                        className="bg-orange-500 h-2 rounded-full transition-all"
                                        style={{ width: `${source.tone_bias.sensational * 100}%` }}
                                    />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-600 dark:text-gray-400">Factual</span>
                                    <span className="font-semibold text-green-600 dark:text-green-400">
                                        {(source.tone_bias.factual * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div
                                        className="bg-green-500 h-2 rounded-full transition-all"
                                        style={{ width: `${source.tone_bias.factual * 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Sample Excerpts Toggle */}
                {source.sample_excerpts.length > 0 && (
                    <div>
                        <button
                            onClick={() => setShowExcerpts(!showExcerpts)}
                            className="w-full flex items-center justify-between px-4 py-3 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                        >
                            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                Sample Article Excerpts ({source.sample_excerpts.length})
                            </span>
                            <svg
                                className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${showExcerpts ? 'rotate-180' : ''
                                    }`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        {/* Excerpts List */}
                        {showExcerpts && (
                            <div className="mt-4 space-y-4">
                                {source.sample_excerpts.map((excerpt, idx) => (
                                    <div
                                        key={idx}
                                        className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-700/30 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
                                    >
                                        {/* Polarization Score Badge */}
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center space-x-2">
                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${excerpt.polarization_score >= 70
                                                        ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                                        : excerpt.polarization_score >= 50
                                                            ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300'
                                                            : excerpt.polarization_score >= 30
                                                                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                                                                : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                                    }`}>
                                                    🔥 {excerpt.polarization_score.toFixed(0)}
                                                </span>
                                                {/* Topic Tags */}
                                                {excerpt.topic_tags.slice(0, 2).map((tag, tagIdx) => (
                                                    <span
                                                        key={tagIdx}
                                                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                                {formatDate(excerpt.timestamp)}
                                            </span>
                                        </div>

                                        {/* Headline (Primary Content) */}
                                        <a
                                            href={excerpt.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block mb-3 group"
                                        >
                                            <h5 className="font-bold text-gray-900 dark:text-white text-base group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors leading-snug">
                                                {excerpt.title}
                                            </h5>
                                        </a>

                                        {/* Highlighted Keywords */}
                                        {excerpt.highlighted_keywords.length > 0 && (
                                            <div className="flex flex-wrap gap-1.5 mb-3">
                                                <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">
                                                    Keywords:
                                                </span>
                                                {excerpt.highlighted_keywords.map((keyword, keyIdx) => (
                                                    <span
                                                        key={keyIdx}
                                                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 border border-red-200 dark:border-red-800"
                                                    >
                                                        {keyword}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {/* Summary (Collapsed Context) */}
                                        {excerpt.summary && excerpt.summary.length > 0 && (
                                            <details className="group/details">
                                                <summary className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300 flex items-center space-x-1">
                                                    <span>Show context</span>
                                                    <svg
                                                        className="w-3 h-3 transition-transform group-open/details:rotate-180"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        viewBox="0 0 24 24"
                                                    >
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                    </svg>
                                                </summary>
                                                <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 pl-2 border-l-2 border-gray-300 dark:border-gray-600">
                                                    {excerpt.summary}
                                                </p>
                                            </details>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

