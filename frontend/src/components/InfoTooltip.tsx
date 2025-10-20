'use client';

import { useState } from 'react';

interface InfoTooltipProps {
    content: string;
}

export default function InfoTooltip({ content }: InfoTooltipProps) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div className="relative inline-block">
            <button
                type="button"
                className="inline-flex items-center justify-center w-4 h-4 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 cursor-help transition-colors"
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                onClick={() => setIsVisible(!isVisible)}
            >
                ℹ️
            </button>

            {isVisible && (
                <div className="absolute left-0 top-6 z-50 w-80 p-3 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg shadow-xl border border-gray-700">
                    <div className="whitespace-pre-line">{content}</div>
                    <div className="absolute -top-2 left-2 w-3 h-3 bg-gray-900 dark:bg-gray-800 border-l border-t border-gray-700 transform rotate-45" />
                </div>
            )}
        </div>
    );
}

