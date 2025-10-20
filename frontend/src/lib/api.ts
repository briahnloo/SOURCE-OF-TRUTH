/**
 * API client for Truth Layer backend
 */

// Use Docker service name for SSR (server-side), localhost for client-side
function getApiUrl(): string {
    // Check if we're running on the server (SSR)
    if (typeof window === 'undefined') {
        // Server-side: use 127.0.0.1 (localhost sometimes fails in Node.js SSR)
        return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    }
    // Client-side: use localhost  
    return 'http://localhost:8000';
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

export interface Event {
    id: number;
    summary: string;
    articles_count: number;
    unique_sources: number;
    truth_score: number;
    confidence_tier: string;
    underreported: boolean;
    coherence_score?: number;
    has_conflict?: boolean;
    conflict_severity?: string;
    conflict_explanation?: ConflictExplanation;
    bias_compass?: BiasCompass;
    category?: string;
    category_confidence?: number;
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
    underreported_events: number;
    conflict_events: number;
    avg_confidence_score: number;
    avg_coherence_score: number;
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

    try {
        const response = await fetch(url, {
            cache: 'no-store',  // Disable Next.js caching for dynamic data
            next: { revalidate: 0 }  // Always fetch fresh data
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
        underreported?: boolean;
    }): Promise<EventsResponse> {
        const queryParams = new URLSearchParams();
        if (params?.status) queryParams.set('status', params.status);
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.offset) queryParams.set('offset', params.offset.toString());
        if (params?.underreported !== undefined)
            queryParams.set('underreported', params.underreported.toString());

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
     * Get underreported events
     */
    async getUnderreported(params?: {
        limit?: number;
        offset?: number;
    }): Promise<EventsResponse> {
        const queryParams = new URLSearchParams();
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.offset) queryParams.set('offset', params.offset.toString());

        const query = queryParams.toString();
        return fetchAPI<EventsResponse>(`/events/underreported${query ? `?${query}` : ''}`);
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
};
