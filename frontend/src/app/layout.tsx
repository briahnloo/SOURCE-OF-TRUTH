import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import NavLink from '@/components/NavLink';
import MobileMenu from '@/components/MobileMenu';
import { SearchBar } from '@/components/SearchBar';

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
                            {/* Desktop header */}
                            <div className="hidden md:flex items-center justify-between h-16">
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

                                <nav className="flex items-center space-x-1">
                                    <NavLink href="/">Confirmed</NavLink>
                                    <NavLink href="/developing">Developing</NavLink>
                                    <NavLink href="/conflicts">Conflicts</NavLink>
                                    <NavLink href="/polarizing">Polarizing</NavLink>
                                    <NavLink href="/flagged">Flagged</NavLink>
                                    <NavLink href="/stats">Stats</NavLink>
                                </nav>

                                {/* Search Bar */}
                                <SearchBar />
                            </div>

                            {/* Mobile header */}
                            <div className="md:hidden">
                                <div className="flex items-center justify-between h-14">
                                    <Link href="/" className="flex items-center space-x-2 group">
                                        <div className="w-10 h-10 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 rounded-lg flex items-center justify-center shadow-lg">
                                            <span className="text-white font-bold text-lg">T</span>
                                        </div>
                                        <h1 className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                                            Truthboard
                                        </h1>
                                    </Link>
                                    <MobileMenu />
                                </div>
                                {/* Mobile search bar - full width */}
                                <div className="px-0 py-2">
                                    <SearchBar />
                                </div>
                            </div>
                        </div>
                    </header>

                    {/* Main content */}
                    <main className="flex-1">
                        {children}
                    </main>

                    {/* Footer */}
                    <footer className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 border-t border-gray-200/50 dark:border-gray-700/50 mt-16">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8 mb-8">
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
                                            href="https://github.com/briahnloo"
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

                            <div className="border-t border-gray-200 dark:border-gray-700 pt-6 sm:pt-8">
                                <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0 text-center sm:text-left">
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
