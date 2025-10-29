'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import EventCard from '@/components/EventCard';
import type { EventsResponse } from '@/lib/api';

export default function SearchContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 100);
  const offset = Math.max(parseInt(searchParams.get('offset') || '0'), 0);

  const [events, setEvents] = useState<EventsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function performSearch() {
      setLoading(true);
      setError(null);

      try {
        if (query.trim().length === 0) {
          setEvents({ total: 0, results: [], limit, offset });
        } else {
          const results = await api.searchEvents({
            q: query,
            limit,
            offset,
          });
          setEvents(results);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch search results');
        setEvents({ total: 0, results: [], limit, offset });
      } finally {
        setLoading(false);
      }
    }

    performSearch();
  }, [query, limit, offset]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search Header */}
      <div className="mb-8">
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 dark:from-white dark:via-gray-100 dark:to-gray-300 bg-clip-text text-transparent mb-4">
          Search Results
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-4">
          {query && <span>Searching for: <span className="font-semibold">&quot;{query}&quot;</span></span>}
        </p>

        {/* Results Summary */}
        {query && events && !loading && (
          <div className="space-y-4">
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Found {events.total} event{events.total !== 1 ? 's' : ''}
            </p>

            {/* Search Context Guide */}
            {events.total > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div>
                  <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2 flex items-center gap-2">
                    <span>💡</span>
                    <span>What these results show</span>
                  </h3>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    <li>• All events mentioning &quot;{query}&quot; across news sources</li>
                    <li>• Coverage intensity and source diversity</li>
                    <li>• How different outlets frame the same story</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2 flex items-center gap-2">
                    <span>🔍</span>
                    <span>How to use these results</span>
                  </h3>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    <li>• Click any event to see all perspectives</li>
                    <li>• Compare how different sources cover it</li>
                    <li>• Check for narrative conflicts or gaps</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <p className="text-lg text-gray-400 dark:text-gray-500">
            Searching...
          </p>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-700 dark:text-red-300 font-medium">
            Error: {error}
          </p>
        </div>
      )}

      {/* No Query Message */}
      {!query && !loading && (
        <div className="text-center py-12">
          <p className="text-lg text-gray-500 dark:text-gray-400">
            Enter a search query in the search bar to find events.
          </p>
        </div>
      )}

      {/* No Results Message */}
      {query && events && events.total === 0 && !error && !loading && (
        <div className="text-center py-12">
          <p className="text-lg text-gray-500 dark:text-gray-400 mb-4">
            No events found matching your search.
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Try different keywords or search terms.
          </p>
        </div>
      )}

      {/* Results Grid */}
      {events && events.total > 0 && !loading && (
        <>
          <div className="max-w-6xl mx-auto">
            <div className="grid gap-8 mb-12">
              {events.results.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          </div>

          {/* Pagination Info */}
          {events.total > limit && (
            <div className="text-center text-sm text-gray-600 dark:text-gray-400">
              Showing {offset + 1} to {Math.min(offset + limit, events.total)} of {events.total} results
            </div>
          )}
        </>
      )}
    </div>
  );
}
