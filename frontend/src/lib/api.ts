/**
 * API client for Truth Layer backend
 */

// Use environment variable for production, localhost for development
function getApiUrl(): string {
    // Server-side rendering: use internal Docker service name
    if (typeof window === 'undefined') {
        // Use INTERNAL_API_URL for server-side (Docker service name)
        return process.env.INTERNAL_API_URL || 'http://backend:8000';
    }

    // Client-side: use public API URL or localhost
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

// Check if backend is available
async function isBackendAvailable(): Promise<boolean> {
    try {
        const response = await fetch(`${getApiUrl()}/health`, {
            timeout: 5000,
        });
        return response.ok;
    } catch {
        return false;
    }
}

export interface EventSource {
    domain: string;
    title: string;
    url?: string;
    political_bias?: { left: number; center: number; right: number };
}

export interface ArticleExcerpt {
    source: string;
    title: string;
    url: string;
    excerpt: string;
    relevance_score: number;
}

export interface NarrativePerspective {
    sources: string[];
    article_count: number;
    representative_title: string;
    key_entities: string[];
    sentiment: string;
    focus_keywords: string[];
    political_leaning?: string;
    representative_excerpts?: ArticleExcerpt[];
}

export interface ConflictExplanation {
    perspectives: NarrativePerspective[];
    key_difference: string;
    difference_type: string;
}

export interface BiasCompass {
    geographic: { western: number; eastern: number; global_south: number };
    political: { left: number; center: number; right: number };
    tone: { sensational: number; factual: number };
    detail: { surface: number; deep: number };
}

export interface InternationalSource {
    domain: string;
    country: string;
    region: string;
    article_count: number;
    political_bias: { left: number; center: number; right: number };
}

export interface InternationalCoverage {
    has_international: boolean;
    source_count: number;
    sources: InternationalSource[];
    regional_breakdown: { [region: string]: number };
    political_distribution: { left: number; center: number; right: number };
    coverage_gap_score: number;
    differs_from_us: boolean;
}

export interface Event {
    id: number;
    summary: string;
    articles_count: number;
    unique_sources: number;
    truth_score: number;
    confidence_tier: string;
    has_conflict?: boolean;
    conflict_severity?: string;
    conflict_explanation?: ConflictExplanation;
    bias_compass?: BiasCompass;
    category?: string;
    category_confidence?: number;
    importance_score?: number;
    international_coverage?: InternationalCoverage;
    first_seen: string;
    last_seen: string;
    sources?: EventSource[];
}

export interface EventDetail extends Event {
    geo_diversity?: number;
    evidence_flag: boolean;
    official_match: boolean;
    languages?: string[];
    articles: Article[];
    scoring_breakdown?: ScoringBreakdown;
}

export interface FactCheckFlag {
    claim: string;
    verdict: string;
    evidence_source: string;
    evidence_url?: string;
    explanation: string;
    confidence: number;
    claim_context?: string;
    claim_location?: string;
}

export interface FlaggedArticle {
    id: number;
    source: string;
    title: string;
    url: string;
    timestamp: string;
    fact_check_status: string;
    fact_check_flags: FactCheckFlag[];
}

export interface SourceErrorStats {
    domain: string;
    flagged_count: number;
    false_count: number;
    disputed_count: number;
    total_articles: number;
    error_rate: number;
    impact_score: number;
}

export interface FlaggedArticlesResponse {
    total: number;
    limit: number;
    offset: number;
    articles: FlaggedArticle[];
    source_stats: SourceErrorStats[];
    summary: { [key: string]: number };
}

export interface Article {
    id: number;
    source: string;
    title: string;
    url: string;
    timestamp: string;
    summary?: string;
    entities?: string[];
    fact_check_status?: string;
    fact_check_flags?: FactCheckFlag[];
}

export interface ScoringBreakdown {
    source_diversity: ScoreComponent;
    geo_diversity: ScoreComponent;
    primary_evidence: ScoreComponent;
    official_match: ScoreComponent;
}

export interface ScoreComponent {
    value: number;
    weight: number;
    explanation: string;
}

export interface EventsResponse {
    total: number;
    limit: number;
    offset: number;
    results: Event[];
}

export interface StatsResponse {
    total_events: number;
    total_articles: number;
    confirmed_events: number;
    developing_events: number;
    conflict_events: number;
    avg_confidence_score: number;
    last_ingestion?: string;
    sources_count: number;
    coverage_by_tier: {
        confirmed: number;
        developing: number;
        unverified: number;
    };
    top_sources: Array<{ domain: string; article_count: number }>;
}

export interface HealthResponse {
    status: string;
    database: string;
    worker_last_run?: string;
    total_events: number;
    total_articles: number;
}

export interface PolarizingExcerpt {
    title: string;
    url: string;
    summary: string;
    timestamp: string;
    polarization_score: number;
    highlighted_keywords: string[];
    topic_tags: string[];
}

export interface PolarizingSource {
    domain: string;
    polarization_score: number;
    political_bias: { left: number; center: number; right: number };
    tone_bias: { sensational: number; factual: number };
    article_count: number;
    sample_excerpts: PolarizingExcerpt[];
}

export interface PolarizingSourcesResponse {
    total_sources: number;
    sources: PolarizingSource[];
    methodology: string;
}

class APIError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.status = status;
        this.name = 'APIError';
    }
}

async function fetchAPI<T>(endpoint: string): Promise<T> {
    const url = `${getApiUrl()}${endpoint}`;

    // Check if backend is available first (only during SSR)
    if (typeof window === 'undefined') {
        const isAvailable = await isBackendAvailable();
        if (!isAvailable) {
            throw new Error(`Backend is not available. Please ensure the backend service is running and accessible at ${getApiUrl()}.`);
        }
    }

    try {
        const response = await fetch(url, {
            cache: 'no-store',  // Disable Next.js caching for dynamic data
            timeout: 10000,  // 10 second timeout
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
                response.status
            );
        }

        return await response.json();
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        // More specific error handling
        if (error instanceof TypeError && error.message.includes('fetch failed')) {
            throw new Error(`Network error: Unable to connect to API at ${url}. Please ensure the backend is running.`);
        }
        throw new Error(`Failed to fetch from API: ${error}`);
    }
}

export const api = {
    /**
     * Get paginated list of events
     */
    async getEvents(params?: {
        status?: 'confirmed' | 'developing' | 'all';
        limit?: number;
        offset?: number;
    }): Promise<EventsResponse> {
        const queryParams = new URLSearchParams();
        if (params?.status) queryParams.set('status', params.status);
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.offset) queryParams.set('offset', params.offset.toString());

        const query = queryParams.toString();
        return fetchAPI<EventsResponse>(`/events${query ? `?${query}` : ''}`);
    },

    /**
     * Get detailed information for a specific event
     */
    async getEventDetail(id: number): Promise<EventDetail> {
        return fetchAPI<EventDetail>(`/events/${id}`);
    },

    /**
     * Get events with narrative conflicts
     */
    async getConflicts(params?: { limit?: number; offset?: number }): Promise<EventsResponse> {
        const queryParams = new URLSearchParams();
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.offset) queryParams.set('offset', params.offset.toString());

        const query = queryParams.toString();
        return fetchAPI<EventsResponse>(`/events/conflicts${query ? `?${query}` : ''}`);
    },

    /**
     * Get aggregate statistics
     */
    async getStats(): Promise<StatsResponse> {
        return fetchAPI<StatsResponse>('/events/stats/summary');
    },

    /**
     * Get flagged articles (fact-check failures)
     */
    async getFlaggedArticles(params?: {
        severity?: 'false' | 'disputed' | 'all';
        limit?: number;
        offset?: number;
        source?: string;
        days?: number;
    }): Promise<FlaggedArticlesResponse> {
        const queryParams = new URLSearchParams();
        if (params?.severity) queryParams.set('severity', params.severity);
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.offset) queryParams.set('offset', params.offset.toString());
        if (params?.source) queryParams.set('source', params.source);
        if (params?.days) queryParams.set('days', params.days.toString());

        const query = queryParams.toString();
        return fetchAPI<FlaggedArticlesResponse>(`/events/flagged${query ? `?${query}` : ''}`);
    },

    /**
     * Check system health
     */
    async getHealth(): Promise<HealthResponse> {
        return fetchAPI<HealthResponse>('/health');
    },

    /**
     * Get polarizing sources ranked by political rhetoric
     */
    async getPolarizingSources(params?: {
        min_articles?: number;
        limit?: number;
    }): Promise<PolarizingSourcesResponse> {
        const queryParams = new URLSearchParams();
        if (params?.min_articles) queryParams.set('min_articles', params.min_articles.toString());
        if (params?.limit) queryParams.set('limit', params.limit.toString());

        const query = queryParams.toString();
        return fetchAPI<PolarizingSourcesResponse>(`/events/polarizing-sources${query ? `?${query}` : ''}`);
    },
};
