import { api } from '@/lib/api';
import DevelopingPageClient from '@/components/DevelopingPageClient';

export const dynamic = 'force-dynamic';

export default async function DevelopingPage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getEvents({
            status: 'developing',
            limit: 50,
        });
        events = response.results;
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to fetch events';
        console.error('Error fetching events:', e);
    }

    return <DevelopingPageClient events={events} error={error} />;
}
