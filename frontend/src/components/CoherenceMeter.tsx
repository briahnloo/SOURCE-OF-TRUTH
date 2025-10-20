'use client';

import InfoTooltip from './InfoTooltip';

interface CoherenceMeterProps {
    score: number;
}

export default function CoherenceMeter({ score }: CoherenceMeterProps) {
    const getColor = () => {
        if (score >= 80) return 'from-green-500 to-green-300';
        if (score >= 60) return 'from-yellow-500 to-yellow-300';
        return 'from-red-500 to-red-300';
    };

    const getTextColor = () => {
        if (score >= 80) return 'text-green-700 dark:text-green-400';
        if (score >= 60) return 'text-yellow-700 dark:text-yellow-400';
        return 'text-red-700 dark:text-red-400';
    };

    const getLabel = () => {
        if (score >= 80) return 'Sources agree';
        if (score >= 60) return 'Normal variation';
        if (score >= 40) return 'Different perspectives';
        return 'Major disagreement';
    };

    return (
        <div className="space-y-2">
            <div className="flex justify-between items-center">
                <div className="flex items-center space-x-1">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                        Story Consistency
                    </span>
                    <InfoTooltip content={`Story Consistency measures how similarly sources describe the same event:

80-100 (High) = Sources tell the same story with consistent facts
60-79 (Medium) = Normal reporting variations, same core story
40-59 (Low) = Sources emphasize different aspects or angles
0-39 (Very Low) = Major disagreement - sources contradict each other

Low scores don't mean misinformation, just different perspectives.`} />
                </div>
                <span className={`text-sm font-bold tabular-nums ${getTextColor()}`}>
                    {score.toFixed(1)}
                </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                    className={`h-2 bg-gradient-to-r ${getColor()} rounded-full transition-all duration-500`}
                    style={{ width: `${score}%` }}
                />
            </div>
            <div className="flex justify-between items-start">
                <p className={`text-xs font-semibold ${getTextColor()}`}>{getLabel()}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">{score >= 60 ? 'Normal variation' : 'Multiple angles'}</p>
            </div>
        </div>
    );
}


