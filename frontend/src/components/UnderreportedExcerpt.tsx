'use client';

interface ArticleExcerpt {
    source: string;
    title: string;
    url: string;
    excerpt: string;
    relevance_score: number;
}

interface Perspective {
    representative_excerpts?: ArticleExcerpt[];
}

interface ConflictExplanation {
    perspectives: Perspective[];
}

interface Props {
    conflictExplanation: ConflictExplanation;
}

export default function UnderreportedExcerpt({ conflictExplanation }: Props) {
    const excerpts = conflictExplanation.perspectives[0]?.representative_excerpts;

    if (!excerpts || excerpts.length === 0) {
        return null;
    }

    return (
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
            <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-200 mb-4 flex items-center gap-2">
                <span>📰</span>
                Key Coverage
            </h3>

            <div className="space-y-4">
                {excerpts.slice(0, 3).map((excerpt, idx) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-purple-100 dark:border-purple-900">
                        <blockquote className="text-gray-800 dark:text-gray-200 italic mb-3 text-sm leading-relaxed border-l-4 border-purple-400 pl-4">
                            &quot;{excerpt.excerpt}&quot;
                        </blockquote>
                        <a
                            href={excerpt.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-purple-600 dark:text-purple-400 hover:underline font-medium flex items-center gap-1"
                        >
                            <span>— {excerpt.source}</span>
                            <span>↗</span>
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
}

