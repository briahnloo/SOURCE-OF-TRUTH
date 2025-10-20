'use client';

interface PoliticalBias {
    left: number;
    center: number;
    right: number;
}

interface Source {
    domain: string;
    political_bias?: PoliticalBias;
}

interface Props {
    sources: Source[];
}

export default function PerspectiveBadge({ sources }: Props) {
    // Count sources by political leaning
    const counts = {
        left: 0,
        center: 0,
        right: 0,
    };

    // Deduplicate sources by domain
    const uniqueSources = new Map<string, Source>();
    sources.forEach((source) => {
        if (!uniqueSources.has(source.domain)) {
            uniqueSources.set(source.domain, source);
        }
    });

    // Categorize each unique source
    uniqueSources.forEach((source) => {
        if (source.political_bias) {
            const { left, center, right } = source.political_bias;
            // Determine dominant leaning
            if (left > center && left > right) {
                counts.left++;
            } else if (right > center && right > left) {
                counts.right++;
            } else {
                counts.center++;
            }
        }
    });

    // If no political bias data, don't show the badge
    if (counts.left === 0 && counts.center === 0 && counts.right === 0) {
        return null;
    }

    return (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-medium border border-gray-300 dark:border-gray-600">
            {counts.left > 0 && (
                <span className="flex items-center gap-1">
                    <span className="text-blue-600 dark:text-blue-400">🔵</span>
                    <span className="text-gray-700 dark:text-gray-300">{counts.left}</span>
                </span>
            )}
            {counts.center > 0 && (
                <span className="flex items-center gap-1">
                    <span className="text-gray-500">⚪</span>
                    <span className="text-gray-700 dark:text-gray-300">{counts.center}</span>
                </span>
            )}
            {counts.right > 0 && (
                <span className="flex items-center gap-1">
                    <span className="text-red-600 dark:text-red-400">🔴</span>
                    <span className="text-gray-700 dark:text-gray-300">{counts.right}</span>
                </span>
            )}
        </div>
    );
}

