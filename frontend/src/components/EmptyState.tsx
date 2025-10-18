import Link from 'next/link';

interface EmptyStateProps {
    title?: string;
    message?: string;
    actionText?: string;
    actionHref?: string;
}

export default function EmptyState({
    title = 'No events found',
    message = 'Check back soon - the worker ingests new articles every 15 minutes',
    actionText,
    actionHref,
}: EmptyStateProps) {
    return (
        <div className="card text-center py-16">
            <div className="mb-6">
                <svg
                    className="mx-auto h-24 w-24 text-gray-300 dark:text-gray-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {title}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-6">
                {message}
            </p>
            {actionText && actionHref && (
                <Link href={actionHref} className="btn-primary inline-block">
                    {actionText}
                </Link>
            )}
        </div>
    );
}
