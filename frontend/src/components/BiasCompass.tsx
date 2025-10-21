'use client';

import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { useState } from 'react';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PoliticalBias {
    left: number;
    center: number;
    right: number;
}

interface Source {
    domain: string;
    title: string;
    political_bias?: PoliticalBias;
}

interface Props {
    sources: Source[];
}

export default function BiasCompass({ sources }: Props) {
    const [showInfo, setShowInfo] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);

    const handleToggle = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('BiasCompass toggle clicked, current state:', isExpanded);
        setIsExpanded(prev => !prev);
    };

    // Deduplicate sources by domain and count articles
    const sourceMap = new Map<string, { source: Source; count: number }>();

    sources.forEach((source) => {
        if (source.political_bias) {
            const existing = sourceMap.get(source.domain);
            if (existing) {
                existing.count += 1;
            } else {
                sourceMap.set(source.domain, { source, count: 1 });
            }
        }
    });

    const uniqueSourcesWithBias = Array.from(sourceMap.values());

    if (uniqueSourcesWithBias.length === 0) {
        return null; // Don't show component if no sources have bias data
    }

    const createPieData = (bias: PoliticalBias) => ({
        labels: ['Left', 'Center', 'Right'],
        datasets: [
            {
                data: [bias.left * 100, bias.center * 100, bias.right * 100],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)', // Blue for left/liberal
                    'rgba(156, 163, 175, 0.8)', // Gray for center
                    'rgba(239, 68, 68, 0.8)', // Red for right/conservative
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(156, 163, 175, 1)',
                    'rgba(239, 68, 68, 1)',
                ],
                borderWidth: 1,
            },
        ],
    });

    const pieOptions: any = {
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: function (context: any) {
                        return context.label + ': ' + context.parsed.toFixed(0) + '%';
                    },
                },
            },
        },
        maintainAspectRatio: true,
        responsive: true,
    };

    return (
        <div className="mt-4">
            <button
                onClick={handleToggle}
                className="w-full text-left px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-lg border border-gray-200 dark:border-gray-600 relative z-50 cursor-pointer"
                type="button"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">🎯</span>
                        <span className="font-semibold text-gray-900 dark:text-white text-sm">
                            Source Political Leaning
                        </span>
                    </div>
                    <span className="text-gray-500 dark:text-gray-400">
                        {isExpanded ? '▼' : '▶'}
                    </span>
                </div>
            </button>

            {isExpanded && (
                <div className="card mt-2 animate-fade-in">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <span>🎯</span>
                            Political Bias by Source
                        </h3>
                        <button
                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                            onClick={() => setShowInfo(!showInfo)}
                        >
                            {showInfo ? 'Hide info' : 'What is this?'}
                        </button>
                    </div>

                    {showInfo && (
                        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-xs text-blue-800 dark:text-blue-300">
                            <p className="mb-2">
                                <strong>Political Bias</strong> shows each source&apos;s typical political
                                positioning based on AllSides.com community ratings:
                            </p>
                            <ul className="space-y-1 ml-4">
                                <li>
                                    • <span className="text-blue-600 dark:text-blue-400">Left</span>: Liberal
                                    or progressive perspectives
                                </li>
                                <li>
                                    • <span className="text-gray-600 dark:text-gray-400">Center</span>:
                                    Balanced or neutral coverage
                                </li>
                                <li>
                                    • <span className="text-red-600 dark:text-red-400">Right</span>:
                                    Conservative perspectives
                                </li>
                            </ul>
                            <p className="mt-2">
                                Most sources lean toward one side but include elements of all perspectives.
                            </p>
                        </div>
                    )}

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                        {uniqueSourcesWithBias.map(({ source, count }, idx) => {
                            if (!source.political_bias) return null;

                            const data = createPieData(source.political_bias);

                            // Determine dominant bias
                            const biases = source.political_bias;
                            const dominant =
                                biases.left > biases.center && biases.left > biases.right
                                    ? 'left'
                                    : biases.right > biases.center && biases.right > biases.left
                                        ? 'right'
                                        : 'center';

                            const getBadgeColor = () => {
                                if (dominant === 'left')
                                    return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
                                if (dominant === 'right')
                                    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
                                return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
                            };

                            return (
                                <div
                                    key={source.domain}
                                    className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
                                >
                                    <div className="mb-2">
                                        <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate mb-1">
                                            {source.domain}
                                        </div>
                                        <div className="flex items-center gap-1 flex-wrap">
                                            <span className={`text-xs px-2 py-0.5 rounded ${getBadgeColor()}`}>
                                                {dominant === 'left' && 'Left'}
                                                {dominant === 'center' && 'Center'}
                                                {dominant === 'right' && 'Right'}
                                            </span>
                                            {count > 1 && (
                                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                                    ({count} articles)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="w-full max-w-[120px] mx-auto">
                                        <Pie data={data} options={pieOptions} />
                                    </div>
                                    <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                                        <div className="flex justify-between">
                                            <span className="text-blue-600 dark:text-blue-400">L:</span>
                                            <span>{(biases.left * 100).toFixed(0)}%</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">C:</span>
                                            <span>{(biases.center * 100).toFixed(0)}%</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-red-600 dark:text-red-400">R:</span>
                                            <span>{(biases.right * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

