import { api } from '@/lib/api';
import ConflictsPageClient from '@/components/ConflictsPageClient';

export const dynamic = 'force-dynamic';

export default async function ConflictsPage() {
    let events: any[] = [];
    let error: string | null = null;

    try {
        const response = await api.getConflicts({ limit: 50 });
        events = response.results;
    } catch (err) {
        error = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Error fetching conflicts:', err);
    }

    return <ConflictsPageClient events={events} error={error} />;
}
