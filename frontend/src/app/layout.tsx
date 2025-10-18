import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import NavLink from '@/components/NavLink';

export const metadata: Metadata = {
    title: 'The Truthboard - Truth Layer for the Internet',
    description: 'Truth-scored news events verified via open data sources',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                <div className="min-h-screen flex flex-col">
                    {/* Header */}
                    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50 shadow-sm">
                        <div className="container mx-auto px-4 py-4">
                            <div className="flex items-center justify-between">
                                <Link href="/" className="flex items-center space-x-3 group">
                                    <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-800 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                                        <span className="text-white font-bold text-xl">T</span>
                                    </div>
                                    <div>
                                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                                            The Truthboard
                                        </h1>
                                        <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                            BETA
                                        </span>
                                    </div>
                                </Link>

                                <nav className="hidden md:flex items-center space-x-2">
                                    <NavLink href="/">Confirmed</NavLink>
                                    <NavLink href="/developing">Developing</NavLink>
                                    <NavLink href="/underreported">Underreported</NavLink>
                                    <NavLink href="/stats">Stats</NavLink>

                                    {/* Health indicator */}
                                    <div className="ml-4 flex items-center space-x-2">
                                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Live</span>
                                    </div>
                                </nav>
                            </div>
                        </div>
                    </header>

                    {/* Main content */}
                    <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
                        {children}
                    </main>

                    {/* Footer */}
                    <footer className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-12">
                        <div className="container mx-auto px-4 py-8">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
                                {/* About */}
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                                        About
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        Truth Layer MVP - Verifying news through open data sources and multi-factor confidence scoring.
                                    </p>
                                </div>

                                {/* Quick Links */}
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                                        Resources
                                    </h3>
                                    <div className="space-y-1">
                                        <a
                                            href="http://localhost:8000/feeds/verified.xml"
                                            className="block text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            RSS Feed
                                        </a>
                                        <a
                                            href="http://localhost:8000/docs"
                                            className="block text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            API Documentation
                                        </a>
                                    </div>
                                </div>

                                {/* Stats */}
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                                        System Status
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        Tracking events from 40+ global sources
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                        Updated every 15 minutes
                                    </p>
                                </div>
                            </div>

                            <div className="text-center text-gray-500 dark:text-gray-500 text-sm border-t border-gray-200 dark:border-gray-800 pt-6">
                                <p>
                                    Built with FastAPI, Next.js, and sentence-transformers • MIT License
                                </p>
                            </div>
                        </div>
                    </footer>
                </div>
            </body>
        </html>
    );
}
