'use client';

import { Event } from '@/lib/api';
import BiasCompass from './BiasCompass';
import CoherenceMeter from './CoherenceMeter';
import ConfidenceMeter from './ConfidenceMeter';
import ConflictExplanation from './ConflictExplanation';
import EvidenceDrawer from './EvidenceDrawer';
import FactCheckWarnings from './FactCheckWarnings';
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

    // Determine visual treatment based on category and scores
    const isNaturalEvent = event.category === 'natural_disaster' || event.category === 'health';
    const hasHighConflict = event.has_conflict && (event.coherence_score ?? 100) < 40;
    const isHighTrust = event.truth_score >= 75 && (event.coherence_score ?? 100) >= 70;

    const cardClasses = [
        'card border-l-4',
        getTierColor(),
        'hover:shadow-lift-lg transition-all duration-300 group',
        isNaturalEvent && 'event-card-natural',
        hasHighConflict && 'event-card-conflict',
        isHighTrust && 'event-card-high-trust',
    ].filter(Boolean).join(' ');

    return (
        <div className={cardClasses}>
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3 group-hover:text-primary-700 dark:group-hover:text-primary-400 transition-colors">
                        {event.summary}
                    </h2>

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

                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                        {event.sources && event.sources.length > 0 && (
                            <PerspectiveBadge sources={event.sources} />
                        )}
                        {hasOfficialSource && event.category !== 'natural_disaster' && (
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

            <div className="mb-4">
                <ConfidenceMeter score={event.truth_score} tier={event.confidence_tier} />
            </div>

            {event.coherence_score !== undefined && event.coherence_score !== null && (
                <div className="mb-4">
                    <CoherenceMeter score={event.coherence_score} />
                </div>
            )}

            {event.has_conflict && event.conflict_severity && (event.coherence_score ?? 100) < 40 && (
                <>
                    <div
                        className={`mt-4 p-3 rounded-lg border-l-4 ${event.conflict_severity === 'high'
                            ? 'bg-red-50 border-red-400 dark:bg-red-900/20 dark:border-red-800'
                            : 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-800'
                            }`}
                    >
                        <div className="flex items-start">
                            <span className="text-2xl mr-2">
                                {event.conflict_severity === 'high' ? '🚨' : '⚠️'}
                            </span>
                            <div className="flex-1">
                                <h4 className="font-semibold text-sm mb-1 text-gray-900 dark:text-white">
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
                        <ConflictExplanation
                            explanation={event.conflict_explanation}
                            severity={event.conflict_severity}
                        />
                    )}
                </>
            )}

            {event.conflict_explanation && (event.coherence_score ?? 100) >= 40 && event.sources && (
                <>
                    <UnbiasedSummary
                        conflictExplanation={event.conflict_explanation}
                        sources={event.sources}
                    />
                    <ConflictExplanation
                        explanation={event.conflict_explanation}
                        severity={event.conflict_severity || 'low'}
                    />
                </>
            )}

            {event.sources && event.sources.length > 0 && (
                <>
                    <BiasCompass sources={event.sources} />
                </>
            )}

            {event.sources && event.sources.length > 0 && (
                <EvidenceDrawer sources={event.sources} />
            )}
        </div>
    );
}
