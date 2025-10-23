"use client";

import { InternationalCoverage } from "@/lib/api";

interface InternationalCoverageProps {
    coverage: InternationalCoverage;
}

export default function InternationalCoverageComponent({ coverage }: InternationalCoverageProps) {
    if (!coverage.has_international) {
        return null;
    }

    const { sources, political_distribution, regional_breakdown } = coverage;

    // Calculate pie chart segments
    const total = political_distribution.left + political_distribution.center + political_distribution.right;
    const leftAngle = (political_distribution.left / total) * 360;
    const centerAngle = (political_distribution.center / total) * 360;
    const rightAngle = (political_distribution.right / total) * 360;

    return (
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <h3 className="font-semibold text-gray-800">International Perspective</h3>
                <span className="text-sm text-gray-600">
                    {coverage.source_count} sources from {Object.keys(regional_breakdown).length} regions
                </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Political Bias Pie Chart */}
                <div className="space-y-3">
                    <h4 className="font-medium text-gray-700">Political Leaning</h4>
                    <div className="flex items-center gap-4">
                        <div className="relative w-20 h-20">
                            <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 40 40">
                                {/* Left segment */}
                                <circle
                                    cx="20"
                                    cy="20"
                                    r="16"
                                    fill="none"
                                    stroke="#3b82f6"
                                    strokeWidth="8"
                                    strokeDasharray={`${(leftAngle / 360) * 100.5} 100.5`}
                                    strokeDashoffset="0"
                                />
                                {/* Center segment */}
                                <circle
                                    cx="20"
                                    cy="20"
                                    r="16"
                                    fill="none"
                                    stroke="#8b5cf6"
                                    strokeWidth="8"
                                    strokeDasharray={`${(centerAngle / 360) * 100.5} 100.5`}
                                    strokeDashoffset={`-${(leftAngle / 360) * 100.5}`}
                                />
                                {/* Right segment */}
                                <circle
                                    cx="20"
                                    cy="20"
                                    r="16"
                                    fill="none"
                                    stroke="#ef4444"
                                    strokeWidth="8"
                                    strokeDasharray={`${(rightAngle / 360) * 100.5} 100.5`}
                                    strokeDashoffset={`-${((leftAngle + centerAngle) / 360) * 100.5}`}
                                />
                            </svg>
                        </div>
                        <div className="space-y-1">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                                <span className="text-sm text-gray-600">
                                    Left: {Math.round(political_distribution.left * 100)}%
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                                <span className="text-sm text-gray-600">
                                    Center: {Math.round(political_distribution.center * 100)}%
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                                <span className="text-sm text-gray-600">
                                    Right: {Math.round(political_distribution.right * 100)}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Sources List */}
                <div className="space-y-3">
                    <h4 className="font-medium text-gray-700">Sources by Region</h4>
                    <div className="space-y-2">
                        {sources.map((source, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">{source.domain}</span>
                                    <span className="text-gray-500">({source.country})</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className="text-gray-600">{source.article_count} articles</span>
                                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Regional Breakdown */}
            {Object.keys(regional_breakdown).length > 1 && (
                <div className="mt-4 pt-3 border-t border-blue-200">
                    <h4 className="font-medium text-gray-700 mb-2">Regional Distribution</h4>
                    <div className="flex flex-wrap gap-2">
                        {Object.entries(regional_breakdown).map(([region, count]) => (
                            <span
                                key={region}
                                className="px-2 py-1 bg-blue-200 text-blue-800 text-xs rounded-full"
                            >
                                {region}: {count} sources
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Coverage Gap Indicator */}
            {coverage.differs_from_us && (
                <div className="mt-3 pt-3 border-t border-blue-200">
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span>International coverage differs from US sources</span>
                    </div>
                </div>
            )}
        </div>
    );
}