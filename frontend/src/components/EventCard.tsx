'use client';

import { Event } from '@/lib/api';
import ConfidenceMeter from './ConfidenceMeter';
import EvidenceDrawer from './EvidenceDrawer';

interface EventCardProps {
    event: Event;
}

export default function EventCard({ event }: EventCardProps) {
    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

        if (diffHours < 1) {
            const diffMins = Math.floor(diffMs / (1000 * 60));
            return `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else {
            const diffDays = Math.floor(diffHours / 24);
            return `${diffDays}d ago`;
        }
    };

    const getTierColor = () => {
        if (event.confidence_tier === 'confirmed') return 'border-confirmed';
        if (event.confidence_tier === 'developing') return 'border-developing';
        return 'border-gray-400';
    };

    // Check if event has official sources
    const hasOfficialSource = event.sources?.some((s) =>
        ['usgs.gov', 'who.int', 'nasa.gov', 'unocha.org', 'reliefweb.int'].some((official) =>
            s.domain.includes(official)
        )
    );

    return (
        <div
            className={`card border-l-4 ${getTierColor()} hover:shadow-lift-lg transition-all duration-300 group`}
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3 group-hover:text-primary-700 dark:group-hover:text-primary-400 transition-colors">
                        {event.summary}
                    </h2>

                    {/* Metadata with icons */}
                    <div className="flex items-center flex-wrap gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                            </svg>
                            <span className="font-medium">{event.unique_sources} sources</span>
                        </span>
                        <span>•</span>
                        <span className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                <path
                                    fillRule="evenodd"
                                    d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <span>{event.articles_count} articles</span>
                        </span>
                        <span>•</span>
                        <span className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                    fillRule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <span>{formatDate(event.first_seen)}</span>
                        </span>
                    </div>

                    {/* Badges */}
                    <div className="flex items-center gap-2 mt-3">
                        {hasOfficialSource && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                                🏛️ Official Source
                            </span>
                        )}
                        {event.underreported && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-underreported-100 text-underreported-dark dark:bg-underreported-900/30 dark:text-underreported-light border border-underreported-200 dark:border-underreported-800">
                                📢 Underreported
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Confidence meter */}
            <div className="mb-4">
                <ConfidenceMeter score={event.truth_score} tier={event.confidence_tier} />
            </div>

            {/* Evidence drawer */}
            {event.sources && event.sources.length > 0 && (
                <EvidenceDrawer sources={event.sources} />
            )}
        </div>
    );
}
