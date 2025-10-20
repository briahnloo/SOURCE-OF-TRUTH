import { api } from '@/lib/api';
import EventCard from '@/components/EventCard';
import HeroSection from '@/components/HeroSection';
import EmptyState from '@/components/EmptyState';

export const dynamic = 'force-dynamic'; // Revalidate every 60 seconds

export default async function HomePage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getEvents({
            status: 'confirmed',
            limit: 20,
        });
        events = response.results;
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch events';
        console.error('Error fetching events:', e);
    }

    return (
        <div>
            {/* Hero Welcome Section */}
            <HeroSection />

            {/* Page Title */}
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Top Confirmed Events
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                    Events with confidence scores ≥ 75 verified through multiple sources
                </p>
            </div>

            {error ? (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
                    <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                        Make sure the backend API is running at{' '}
                        {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                    </p>
                </div>
            ) : events.length === 0 ? (
                <EmptyState
                    title="No confirmed events yet"
                    message="Events need high source diversity and official verification to reach confirmed status (≥75). Check the Developing page to see events being verified."
                    actionText="View Developing Events"
                    actionHref="/developing"
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
