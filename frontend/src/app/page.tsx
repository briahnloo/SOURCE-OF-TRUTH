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
            politics_only: true,
        });
        events = response.results;
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch events';
        console.error('Error fetching events:', e);
    }

    return (
        <div className="min-h-screen">
            {/* Hero Welcome Section */}
            <HeroSection />

            {/* Main Content Container */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Page Title Section */}
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 dark:from-white dark:via-gray-100 dark:to-gray-300 bg-clip-text text-transparent mb-4">
                        Top Confirmed Events
                    </h2>
                    <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
                        Events with confidence scores ≥ 75 verified through multiple sources.
                        Each event has been rigorously fact-checked and cross-referenced.
                    </p>
                </div>

                {/* Content Section */}
                {error ? (
                    <div className="max-w-4xl mx-auto">
                        <div className="card-elevated bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                            <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                    <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                                        Connection Error
                                    </h3>
                                    <p className="text-red-700 dark:text-red-300 mb-3">{error}</p>
                                    <p className="text-sm text-red-600 dark:text-red-400">
                                        Backend API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : events.length === 0 ? (
                    <div className="max-w-4xl mx-auto">
                        <EmptyState
                            title="No confirmed events yet"
                            message="Events need high source diversity and official verification to reach confirmed status (≥75). Check the Developing page to see events being verified."
                            actionText="View Developing Events"
                            actionHref="/developing"
                        />
                    </div>
                ) : (
                    <div className="max-w-6xl mx-auto">
                        <div className="grid gap-8">
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
                    </div>
                )}
            </div>
        </div>
    );
}
