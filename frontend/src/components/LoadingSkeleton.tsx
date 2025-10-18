export default function LoadingSkeleton() {
    return (
        <div className="space-y-6">
            {[1, 2, 3].map((i) => (
                <div key={i} className="card animate-pulse">
                    <div className="shimmer h-6 w-3/4 mb-4 rounded"></div>
                    <div className="shimmer h-4 w-1/2 mb-4 rounded"></div>
                    <div className="shimmer h-3 w-full mb-2 rounded"></div>
                    <div className="shimmer h-3 w-5/6 rounded"></div>
                </div>
            ))}
            <p className="text-center text-gray-500 dark:text-gray-400 text-sm">
                Loading verified events...
            </p>
        </div>
    );
}
