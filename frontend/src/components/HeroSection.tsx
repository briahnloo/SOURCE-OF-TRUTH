'use client';

import { useEffect, useState } from 'react';

interface StatBadgeProps {
    icon: string;
    label: string;
    value: string;
}

function StatBadge({ icon, label, value }: StatBadgeProps) {
    return (
        <div className="flex flex-col items-center p-4 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <span className="text-3xl mb-2">{icon}</span>
            <span className="text-2xl font-bold text-white tabular-nums">{value}</span>
            <span className="text-sm text-white/80">{label}</span>
        </div>
    );
}

export default function HeroSection() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(true);
    }, []);

    return (
        <section
            className={`gradient-hero rounded-2xl p-8 md:p-12 mb-12 transition-opacity duration-1000 ${isVisible ? 'opacity-100' : 'opacity-0'
                }`}
        >
            <div className="max-w-4xl mx-auto text-center">
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 animate-slide-up">
                    Welcome, Seekers of Knowledge
                </h1>
                <p className="text-lg md:text-xl text-white/90 mb-8 leading-relaxed">
                    Mathematically unbiased news reporting powered by open data verification.
                    Each page shows truth-scored events from multiple independent sources,
                    clustered by AI and verified against official feeds.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                    <StatBadge icon="🔍" label="Sources Verified" value="42+" />
                    <StatBadge icon="📊" label="Confidence Algorithm" value="4-Factor" />
                    <StatBadge icon="🌍" label="Global Coverage" value="Real-time" />
                </div>

                <div className="mt-8 text-sm text-white/70">
                    <p>
                        Ingesting news every 15 minutes • No bias, no agenda, just truth
                    </p>
                </div>
            </div>
        </section>
    );
}
