import { api } from '@/lib/api';
import EventCard from '@/components/EventCard';
import EmptyState from '@/components/EmptyState';

export const revalidate = 60;

export default async function DevelopingPage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getEvents({
            status: 'developing',
            limit: 20,
        });
        events = response.results;
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch events';
        console.error('Error fetching events:', e);
    }

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    Developing Events
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                    Events with moderate coverage (scores 40-74) currently being verified
                </p>
            </div>

            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                </div>
            ) : events.length === 0 ? (
                <EmptyState
                    title="No developing events at this time"
                    message="Events in this tier have moderate source coverage and are being actively verified. They may be promoted to Confirmed as more sources report."
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
