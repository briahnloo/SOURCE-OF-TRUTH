'use client';

import { useEffect, useState } from 'react';

interface ConfidenceMeterProps {
    score: number;
    tier: string;
}

export default function ConfidenceMeter({ score, tier }: ConfidenceMeterProps) {
    const [animatedScore, setAnimatedScore] = useState(0);

    useEffect(() => {
        // Animate score counting up
        const duration = 1000;
        const steps = 20;
        const increment = score / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= score) {
                setAnimatedScore(score);
                clearInterval(timer);
            } else {
                setAnimatedScore(current);
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [score]);

    // Determine gradient and effects based on tier
    const getGradientClass = () => {
        if (tier === 'confirmed') return 'gradient-confirmed';
        if (tier === 'developing') return 'gradient-developing';
        return 'bg-gray-400';
    };

    const getTextColor = () => {
        if (tier === 'confirmed') return 'text-confirmed-dark';
        if (tier === 'developing') return 'text-developing-dark';
        return 'text-gray-600';
    };

    const getBadgeColor = () => {
        if (tier === 'confirmed')
            return 'bg-confirmed-100 text-confirmed-dark border border-confirmed-light';
        if (tier === 'developing')
            return 'bg-developing-100 text-developing-dark border border-developing-light';
        return 'bg-gray-200 text-gray-700 border border-gray-300';
    };

    const needsGlow = score >= 85;

    return (
        <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            {/* Score label */}
            <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    Confidence Score
                </span>
                <span
                    className={`text-3xl font-bold tabular-nums ${getTextColor()} ${needsGlow ? 'animate-pulse-glow' : ''
                        }`}
                >
                    {animatedScore.toFixed(1)}
                    {needsGlow && <span className="ml-1">⭐</span>}
                </span>
            </div>

            {/* Progress bar with gradient */}
            <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden shadow-inner">
                <div
                    className={`h-full ${getGradientClass()} transition-all duration-1000 ease-out rounded-full ${needsGlow ? 'shadow-glow-md' : ''
                        }`}
                    style={{ width: `${animatedScore}%` }}
                />
            </div>

            {/* Tier badge and threshold info */}
            <div className="flex items-center justify-between">
                <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getBadgeColor()}`}
                >
                    {tier.charAt(0).toUpperCase() + tier.slice(1)}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                    {tier === 'confirmed' && '≥ 75'}
                    {tier === 'developing' && '40-74'}
                    {tier !== 'confirmed' && tier !== 'developing' && '< 40'}
                </span>
            </div>
        </div>
    );
}
