'use client';

import { Event } from '@/lib/api';
import BiasCompass from './BiasCompass';
import ConfidenceMeter from './ConfidenceMeter';
import ConflictExplanation from './ConflictExplanation';
import EvidenceDrawer from './EvidenceDrawer';
import FactCheckWarnings from './FactCheckWarnings';
import InternationalCoverageComponent from './InternationalCoverage';
import PerspectiveBadge from './PerspectiveBadge';
import UnbiasedSummary from './UnbiasedSummary';

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
        if (event.confidence_tier === 'confirmed') return 'border-confirmed-300 dark:border-confirmed-600';
        if (event.confidence_tier === 'developing') return 'border-developing-300 dark:border-developing-600';
        return 'border-gray-300 dark:border-gray-600';
    };

    // Check if event has official sources
    const hasOfficialSource = event.sources?.some((s) =>
        ['usgs.gov', 'who.int', 'nasa.gov', 'unocha.org', 'reliefweb.int'].some((official) =>
            s.domain.includes(official)
        )
    );

    // Determine visual treatment based on category and scores
    const isNaturalEvent = event.category === 'natural_disaster' || event.category === 'health';
    const hasHighConflict = event.has_conflict;
    const isHighTrust = event.truth_score >= 75;

    const cardClasses = [
        'group relative overflow-hidden',
        'bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700',
        'hover:shadow-2xl hover:-translate-y-1 transition-all duration-500',
        'border-l-4',
        getTierColor(),
        isNaturalEvent && 'event-card-natural',
        hasHighConflict && 'event-card-conflict',
        isHighTrust && 'event-card-high-trust',
    ].filter(Boolean).join(' ');

    return (
        <div className={cardClasses}>
            {/* Gradient overlay for hover effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

            {/* Content */}
            <div className="relative p-8">
                {/* Header with title and metadata */}
                <div className="mb-6">
                    <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4 group-hover:text-primary-700 dark:group-hover:text-primary-400 transition-colors leading-tight">
                        {event.summary}
                    </h2>

                    {/* Metadata row */}
                    <div className="flex items-center flex-wrap gap-6 text-sm text-gray-600 dark:text-gray-400">
                        <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                                <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                                </svg>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-900 dark:text-white">{event.unique_sources}</span>
                                <span className="text-gray-500 dark:text-gray-400"> sources</span>
                            </div>
                        </div>

                        <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                                <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                    <path
                                        fillRule="evenodd"
                                        d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-900 dark:text-white">{event.articles_count}</span>
                                <span className="text-gray-500 dark:text-gray-400"> articles</span>
                            </div>
                        </div>

                        <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
                                <svg className="w-4 h-4 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-900 dark:text-white">{formatDate(event.first_seen)}</span>
                                <span className="text-gray-500 dark:text-gray-400"> ago</span>
                            </div>
                        </div>
                    </div>

                    {/* Badges */}
                    <div className="flex items-center gap-3 mt-4 flex-wrap">
                        {event.sources && event.sources.length > 0 && (
                            <PerspectiveBadge sources={event.sources} />
                        )}
                        {hasOfficialSource && event.category !== 'natural_disaster' && (
                            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800 shadow-sm">
                                🏛️ Official Source
                            </span>
                        )}
                    </div>
                </div>

                {/* Metrics Section */}
                <div className="mb-6">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                        <ConfidenceMeter score={event.truth_score} tier={event.confidence_tier} />
                    </div>
                </div>

                {/* Conflict Warning */}
                {event.has_conflict && event.conflict_severity && (
                    <div className="mb-6">
                        <div
                            className={`p-4 rounded-xl border-l-4 ${event.conflict_severity === 'high'
                                ? 'bg-red-50 border-red-400 dark:bg-red-900/20 dark:border-red-800'
                                : 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-800'
                                }`}
                        >
                            <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                    <span className="text-2xl">
                                        {event.conflict_severity === 'high' ? '🚨' : '⚠️'}
                                    </span>
                                </div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-base mb-2 text-gray-900 dark:text-white">
                                        {event.conflict_severity === 'high'
                                            ? 'Major Narrative Conflict'
                                            : 'Sources Show Different Perspectives'}
                                    </h4>
                                    <p className="text-sm text-gray-700 dark:text-gray-300">
                                        Sources describe this event very differently. Read multiple sources for full context.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {event.conflict_explanation && (
                            <div className="mt-4">
                                <ConflictExplanation
                                    explanation={event.conflict_explanation}
                                    severity={event.conflict_severity}
                                />
                            </div>
                        )}
                    </div>
                )}

                {/* Unbiased Summary */}
                {event.conflict_explanation && !event.has_conflict && event.sources && (
                    <div className="mb-6">
                        <UnbiasedSummary
                            conflictExplanation={event.conflict_explanation}
                            sources={event.sources}
                        />
                        <div className="mt-4">
                            <ConflictExplanation
                                explanation={event.conflict_explanation}
                                severity={event.conflict_severity || 'low'}
                            />
                        </div>
                    </div>
                )}

                {/* Bias Analysis and Evidence */}
                <div className="space-y-6">
                    {/* International Coverage */}
                    {event.international_coverage && (
                        <InternationalCoverageComponent coverage={event.international_coverage} />
                    )}

                    {event.sources && event.sources.length > 0 && (
                        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-6">
                            <BiasCompass sources={event.sources} />
                        </div>
                    )}

                    {event.sources && event.sources.length > 0 && (
                        <div>
                            <EvidenceDrawer sources={event.sources} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
