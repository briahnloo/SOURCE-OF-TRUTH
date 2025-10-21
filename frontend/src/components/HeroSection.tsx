'use client';

import { useEffect, useState } from 'react';

interface StatBadgeProps {
    icon: string;
    label: string;
    value: string;
    description: string;
}

function StatBadge({ icon, label, value, description }: StatBadgeProps) {
    return (
        <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex flex-col items-center p-6 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl border border-white/20 dark:border-gray-700/20 hover:bg-white dark:hover:bg-gray-800 transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                <div className="text-4xl mb-3 group-hover:scale-110 transition-transform duration-300">
                    {icon}
                </div>
                <span className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent tabular-nums mb-1">
                    {value}
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {label}
                </span>
                <span className="text-xs text-gray-600 dark:text-gray-400 text-center">
                    {description}
                </span>
            </div>
        </div>
    );
}

export default function HeroSection() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(true);
    }, []);

    return (
        <section className="relative overflow-hidden">
            {/* Background with animated gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-purple-600 to-pink-600"></div>
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent"></div>

            {/* Animated background elements */}
            <div className="absolute top-0 left-0 w-full h-full">
                <div className="absolute top-20 left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-pink-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '4s' }}></div>
            </div>

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
                <div className="text-center">
                    {/* Main heading with gradient text */}
                    <h1 className={`text-5xl md:text-7xl font-bold text-white mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        <span className="bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent">
                            The Truthboard
                        </span>
                    </h1>

                    {/* Subtitle */}
                    <p className={`text-xl md:text-2xl text-white/90 mb-4 max-w-4xl mx-auto leading-relaxed transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        Mathematically unbiased news reporting powered by open data verification
                    </p>

                    {/* Description */}
                    <p className={`text-lg text-white/80 mb-12 max-w-3xl mx-auto leading-relaxed transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        Each event is truth-scored from multiple independent sources, clustered by AI,
                        and verified against official feeds. No bias, no agenda, just truth.
                    </p>

                    {/* Stats Grid */}
                    <div className={`grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        <StatBadge
                            icon="🔍"
                            label="Sources Verified"
                            value="42+"
                            description="Global news sources monitored"
                        />
                        <StatBadge
                            icon="📊"
                            label="Confidence Algorithm"
                            value="4-Factor"
                            description="Multi-dimensional scoring system"
                        />
                        <StatBadge
                            icon="🌍"
                            label="Global Coverage"
                            value="Real-time"
                            description="Updated every 15 minutes"
                        />
                    </div>

                    {/* Status indicator */}
                    <div className={`mt-12 flex items-center justify-center space-x-3 transition-all duration-1000 delay-800 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2">
                            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-sm font-medium text-white">Live System</span>
                        </div>
                        <div className="text-sm text-white/70">
                            Ingesting news every 15 minutes
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
