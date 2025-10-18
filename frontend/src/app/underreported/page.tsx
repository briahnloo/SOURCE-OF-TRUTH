import { api } from '@/lib/api';
import EventCard from '@/components/EventCard';
import EmptyState from '@/components/EmptyState';

export const revalidate = 60;

export default async function UnderreportedPage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getUnderreported({ limit: 20 });
        events = response.results;
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch events';
        console.error('Error fetching underreported events:', e);
    }

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    Underreported Stories
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                    Events covered by NGO/Gov sources but absent from major wire services
                </p>
            </div>

            <div className="card bg-underreported-50 dark:bg-underreported-900/20 border-l-4 border-underreported mb-6">
                <h2 className="text-lg font-semibold text-underreported-dark dark:text-underreported-light mb-2">
                    What are underreported stories?
                </h2>
                <p className="text-gray-700 dark:text-gray-300">
                    These events are documented by official sources (USGS, WHO, UN, ReliefWeb, NASA)
                    or multiple local outlets, but have not been picked up by major international
                    wire services (AP, Reuters, AFP) within 48 hours.
                </p>
            </div>

            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                </div>
            ) : events.length === 0 ? (
                <EmptyState
                    title="No underreported events detected"
                    message="All recent events have been covered by major wire services. This is actually good news - it means mainstream media is doing its job!"
                />
            ) : (
                <div className="space-y-6 animate-fade-in">
                    {events.map((event, idx) => (
                        <div
                            key={event.id}
                            style={{ animationDelay: `${idx * 0.1}s` }}
                            className="animate-slide-up"
                        >
                            <EventCard event={event} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
