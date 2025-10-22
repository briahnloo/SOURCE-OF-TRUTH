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
                    <header className="glass-effect sticky top-0 z-50 border-b border-gray-200/20 dark:border-gray-700/20">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div className="flex items-center justify-between h-16">
                                <Link href="/" className="flex items-center space-x-3 group">
                                    <div className="w-12 h-12 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all duration-300">
                                        <span className="text-white font-bold text-2xl">T</span>
                                    </div>
                                    <div>
                                        <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                                            The Truthboard
                                        </h1>
                                        <div className="flex items-center space-x-2">
                                            <span className="text-xs bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200 px-2 py-1 rounded-full font-semibold">
                                                BETA
                                            </span>
                                            <div className="flex items-center space-x-1">
                                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Live</span>
                                            </div>
                                        </div>
                                    </div>
                                </Link>

                                <nav className="hidden md:flex items-center space-x-1">
                                    <NavLink href="/">Confirmed</NavLink>
                                    <NavLink href="/developing">Developing</NavLink>
                                    <NavLink href="/conflicts">Conflicts</NavLink>
                                    <NavLink href="/polarizing">Polarizing</NavLink>
                                    <NavLink href="/flagged">Flagged</NavLink>
                                    <NavLink href="/stats">Stats</NavLink>
                                </nav>

                                {/* Mobile menu button */}
                                <button className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </header>

                    {/* Main content */}
                    <main className="flex-1">
                        {children}
                    </main>

                    {/* Footer */}
                    <footer className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 border-t border-gray-200/50 dark:border-gray-700/50 mt-16">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                                {/* About */}
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                        About Truthboard
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                                        Verifying news through open data sources and multi-factor confidence scoring.
                                        Our AI-powered system analyzes 40+ global sources to provide unbiased,
                                        fact-checked information.
                                    </p>
                                </div>

                                {/* Quick Links */}
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                        Resources
                                    </h3>
                                    <div className="space-y-2">
                                        <a
                                            href="http://localhost:8000/feeds/verified.xml"
                                            className="block text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            📡 RSS Feed
                                        </a>
                                        <a
                                            href="http://localhost:8000/docs"
                                            className="block text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            📚 API Documentation
                                        </a>
                                        <a
                                            href="https://github.com/your-repo"
                                            className="block text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            💻 GitHub Repository
                                        </a>
                                    </div>
                                </div>

                                {/* Stats */}
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                        System Status
                                    </h3>
                                    <div className="space-y-2">
                                        <div className="flex items-center space-x-2">
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                            <span className="text-sm text-gray-600 dark:text-gray-400">All systems operational</span>
                                        </div>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            Tracking events from 40+ global sources
                                        </p>
                                        <p className="text-xs text-gray-500 dark:text-gray-500">
                                            Updated every 15 minutes
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="border-t border-gray-200 dark:border-gray-700 pt-8">
                                <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        Built with FastAPI, Next.js, and sentence-transformers • MIT License
                                    </p>
                                    <div className="flex items-center space-x-4">
                                        <span className="text-xs text-gray-400">Version 1.0.0 Beta</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </footer>
                </div>
            </body>
        </html>
    );
}
