import { Suspense } from 'react';
import SearchContent from './search-content';

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageLoading />}>
      <SearchContent />
    </Suspense>
  );
}

function SearchPageLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 dark:from-white dark:via-gray-100 dark:to-gray-300 bg-clip-text text-transparent mb-4">
          Search Results
        </h1>
        <p className="text-lg text-gray-400 dark:text-gray-500">
          Loading...
        </p>
      </div>
    </div>
  );
}
