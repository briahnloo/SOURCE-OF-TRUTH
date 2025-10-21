"""Narrative Coherence Score calculation

Detects when sources present conflicting narratives about the same event.
Uses embeddings, entity overlap, and title consistency to measure agreement.
"""

import json
import os
from collections import Counter
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
import spacy
from openai import OpenAI
from app.models import Article
from app.services.content_fetcher import ContentFetcher
from app.services.service_registry import get_nlp_model, get_bias_analyzer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity


def get_nlp():
    """Get the singleton spaCy NLP model instance"""
    return get_nlp_model()


@dataclass
class ArticleExcerpt:
    """Represents a key excerpt from an article showing perspective differences"""
    source: str
    title: str
    url: str
    excerpt: str
    relevance_score: float


@dataclass
class NarrativePerspective:
    """Represents a narrative perspective within a conflicting event"""
    sources: List[str]
    article_count: int
    representative_title: str
    key_entities: List[str]
    sentiment: str  # "negative", "neutral", "positive"
    focus_keywords: List[str]
    political_leaning: Optional[str] = None  # "left", "center", "right"
    representative_excerpts: Optional[List[dict]] = None  # List of ArticleExcerpt as dicts


@dataclass
class NumericDiscrepancy:
    """Represents a numerical difference between perspectives"""
    metric: str  # What's being measured (e.g., "crowd size", "casualties")
    values_by_perspective: dict  # {perspective_idx: value_str}
    significance: str  # "high", "medium", "low"


@dataclass
class ConflictClassification:
    """Classify the nature of a conflict"""
    conflict_type: str  # "numerical", "attribution", "framing", "facts", "interpretation"
    is_factual_dispute: bool  # True if claims contradict facts
    is_framing_difference: bool  # True if same facts, different spin
    confidence: float  # How certain we are about classification


@dataclass
class ConflictExplanation:
    """Explains why sources present different narratives"""
    perspectives: List[dict]  # List of NarrativePerspective as dicts
    key_difference: str
    difference_type: str  # "emphasis", "facts", "interpretation", "framing"
    numeric_discrepancies: Optional[List[dict]] = None  # List of NumericDiscrepancy as dicts
    classification: Optional[dict] = None  # ConflictClassification as dict
    keyword_overlap: Optional[float] = None  # 0-1, higher = more similar perspectives


def calculate_narrative_coherence(
    articles: List[Article], embeddings: np.ndarray
) -> Tuple[float, str, Optional[ConflictExplanation]]:
    """
    Calculate how much sources agree on the narrative of an event.

    Args:
        articles: List of articles in the event cluster
        embeddings: Pre-computed embeddings for the articles

    Returns:
        Tuple of (coherence_score, conflict_severity, explanation)
        - coherence_score: 0-100 (higher = more agreement)
        - conflict_severity: 'none', 'low', 'medium', 'high'
        - explanation: ConflictExplanation if conflict detected, else None
    """
    if len(articles) < 2:
        return 100.0, "none", None  # Single source = no conflict

    # 1. Embedding similarity (60% weight)
    embedding_score = calculate_embedding_similarity(embeddings) * 60

    # 2. Entity overlap (25% weight)
    entity_score = calculate_entity_overlap(articles) * 25

    # 3. Title consistency (15% weight)
    title_score = calculate_title_consistency(articles) * 15

    # Total coherence
    coherence = embedding_score + entity_score + title_score
    coherence = round(min(100, max(0, coherence)), 1)

    # Determine conflict severity
    severity = determine_conflict_severity(coherence)

    # CRITICAL: Only flag as conflict if politically diverse
    if severity != "none":
        # Check if we have left AND right coverage
        politically_diverse = has_political_diversity(articles)
        
        # If not politically diverse, downgrade severity
        if not politically_diverse:
            # Events without left+right coverage are NOT true conflicts
            if len(articles) < 8:
                # Small events without political diversity = no conflict
                severity = "none"
            elif coherence < 40:
                # Only flag single-perspective events if coherence is VERY low
                severity = "low"
            else:
                severity = "none"

    # If conflict detected, generate explanation
    explanation = None
    if severity != "none":
        try:
            # Check if we should use political grouping
            # Use political grouping for high/medium conflict OR when politically diverse
            use_political_grouping = (
                coherence < 60 or has_political_diversity(articles)
            )
            
            if use_political_grouping:
                perspectives, articles_by_perspective = group_by_political_bias(articles)
            else:
                perspectives, articles_by_perspective = identify_narrative_perspectives(articles, embeddings)
            
            explanation = generate_conflict_explanation(perspectives, articles_by_perspective)
        except Exception as e:
            print(f"Warning: Failed to generate conflict explanation: {e}")
            explanation = None

    return coherence, severity, explanation


def calculate_embedding_similarity(embeddings: np.ndarray) -> float:
    """
    Calculate average cosine similarity between all article embeddings.

    Args:
        embeddings: numpy array of embeddings [n_articles, embedding_dim]

    Returns:
        Average similarity score (0-1)
    """
    if len(embeddings) < 2:
        return 1.0

    # Compute pairwise cosine similarity
    sim_matrix = cosine_similarity(embeddings)

    # Get upper triangle (avoid diagonal and duplicates)
    triu_indices = np.triu_indices(len(embeddings), k=1)
    pairwise_sims = sim_matrix[triu_indices]

    # Average similarity
    avg_similarity = float(np.mean(pairwise_sims))

    return avg_similarity


def calculate_entity_overlap(articles: List[Article]) -> float:
    """
    Calculate how much entities overlap across articles.

    Measures if articles mention the same people, places, organizations.

    Args:
        articles: List of articles

    Returns:
        Entity overlap score (0-1)
    """
    if len(articles) < 2:
        return 1.0

    # Extract entities from each article
    article_entities = []

    for article in articles:
        entities = set()

        # Try to get stored entities
        if article.entities_json:
            try:
                stored_entities = json.loads(article.entities_json)
                entities.update([e.lower() for e in stored_entities])
            except:
                pass

        # If no stored entities, extract from title
        if not entities:
            nlp = get_nlp()
            if nlp:
                doc = nlp(article.title)
                entities.update([ent.text.lower() for ent in doc.ents])

        article_entities.append(entities)

    # Calculate pairwise Jaccard similarity
    similarities = []
    for i in range(len(article_entities)):
        for j in range(i + 1, len(article_entities)):
            set_i = article_entities[i]
            set_j = article_entities[j]

            if len(set_i) == 0 and len(set_j) == 0:
                # Both empty = perfect overlap
                similarities.append(1.0)
            elif len(set_i) == 0 or len(set_j) == 0:
                # One empty = no overlap
                similarities.append(0.0)
            else:
                # Jaccard similarity
                intersection = len(set_i & set_j)
                union = len(set_i | set_j)
                similarities.append(intersection / union if union > 0 else 0.0)

    return float(np.mean(similarities)) if similarities else 0.5


def calculate_title_consistency(articles: List[Article]) -> float:
    """
    Calculate how similar article titles are.

    Measures if headlines are aligned on the same story.

    Args:
        articles: List of articles

    Returns:
        Title consistency score (0-1)
    """
    if len(articles) < 2:
        return 1.0

    titles = [article.title.lower() for article in articles]

    # Simple word overlap approach
    # Split titles into words and calculate overlap
    title_words = [set(title.split()) for title in titles]

    # Remove common stop words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
    }

    title_words = [words - stop_words for words in title_words]

    # Calculate pairwise Jaccard similarity
    similarities = []
    for i in range(len(title_words)):
        for j in range(i + 1, len(title_words)):
            set_i = title_words[i]
            set_j = title_words[j]

            if len(set_i) == 0 and len(set_j) == 0:
                similarities.append(1.0)
            elif len(set_i) == 0 or len(set_j) == 0:
                similarities.append(0.0)
            else:
                intersection = len(set_i & set_j)
                union = len(set_i | set_j)
                similarities.append(intersection / union if union > 0 else 0.0)

    return float(np.mean(similarities)) if similarities else 0.5


def determine_conflict_severity(coherence_score: float) -> str:
    """
    Determine conflict severity based on coherence score.
    
    Stricter thresholds to avoid flagging minor title variations as conflicts.

    Args:
        coherence_score: 0-100

    Returns:
        'none', 'low', 'medium', or 'high'
    """
    if coherence_score >= 90:  # Raised from 80
        return "none"  # High coherence, no conflict
    elif coherence_score >= 70:  # Raised from 60
        return "low"  # Moderate coherence, minor differences
    elif coherence_score >= 50:  # Raised from 40
        return "medium"  # Low coherence, significant differences
    else:
        return "high"  # Very low coherence, major conflict


def has_political_diversity(articles: List[Article]) -> bool:
    """
    Check if articles come from sources across the political spectrum.

    Args:
        articles: List of articles

    Returns:
        True if sources span left and right, False otherwise
    """
    try:
        bias_analyzer = get_bias_analyzer()
        
        has_left = False
        has_right = False
        
        for article in articles:
            domain = extract_domain(article.source)
            bias = bias_analyzer.get_source_bias(domain)
            
            if bias:
                political = bias.political
                if political.get('left', 0) > 0.5:
                    has_left = True
                if political.get('right', 0) > 0.5:
                    has_right = True
        
        return has_left and has_right
    except Exception as e:
        print(f"Warning: Could not check political diversity: {e}")
        return False


def group_by_political_bias(articles: List[Article]) -> Tuple[List[NarrativePerspective], List[List[Article]]]:
    """
    Group articles by the political leaning of their source.

    Creates three groups: Left, Center, Right based on source bias classifications.

    Args:
        articles: List of articles

    Returns:
        Tuple of (perspectives, articles_by_perspective)
    """
    try:
        bias_analyzer = get_bias_analyzer()
        
        # Group articles by political leaning
        left_articles = []
        center_articles = []
        right_articles = []
        
        for article in articles:
            domain = extract_domain(article.source)
            bias = bias_analyzer.get_source_bias(domain)
            
            if bias:
                political = bias.political  # BiasScore object, not dict
                left_score = political.get('left', 0)
                center_score = political.get('center', 0)
                right_score = political.get('right', 0)
                
                # Assign to dominant political leaning
                if left_score > center_score and left_score > right_score:
                    left_articles.append(article)
                elif right_score > center_score and right_score > left_score:
                    right_articles.append(article)
                else:
                    center_articles.append(article)
            else:
                # Unknown bias, put in center
                center_articles.append(article)
        
        # Create perspectives for each group that has articles
        perspectives = []
        articles_by_perspective = []
        
        if left_articles:
            perspective = analyze_perspective_group(left_articles)
            perspective.political_leaning = "left"
            perspectives.append(perspective)
            articles_by_perspective.append(left_articles)
        
        if center_articles:
            perspective = analyze_perspective_group(center_articles)
            perspective.political_leaning = "center"
            perspectives.append(perspective)
            articles_by_perspective.append(center_articles)
        
        if right_articles:
            perspective = analyze_perspective_group(right_articles)
            perspective.political_leaning = "right"
            perspectives.append(perspective)
            articles_by_perspective.append(right_articles)
        
        if perspectives:
            return perspectives, articles_by_perspective
        else:
            return [analyze_perspective_group(articles)], [articles]
        
    except Exception as e:
        print(f"Warning: Political grouping failed, falling back to narrative grouping: {e}")
        # Fallback to regular narrative perspectives
        return [analyze_perspective_group(articles)], [articles]


def identify_narrative_perspectives(
    articles: List[Article], embeddings: np.ndarray
) -> Tuple[List[NarrativePerspective], List[List[Article]]]:
    """
    Cluster articles within an event into narrative sub-groups.

    Args:
        articles: List of articles in the event cluster
        embeddings: Pre-computed embeddings for the articles

    Returns:
        Tuple of (perspectives, articles_by_perspective)
    """
    if len(articles) < 3:
        # Too few to meaningfully cluster, create pairwise comparison
        return create_pairwise_comparison(articles, embeddings)

    # Cluster into 2-3 groups (at least 2 articles per group)
    n_clusters = min(3, max(2, len(articles) // 2))

    try:
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters, metric="cosine", linkage="average"
        )

        labels = clustering.fit_predict(embeddings)

        # Build perspective groups
        perspectives = []
        articles_by_perspective = []
        for label in range(n_clusters):
            group_indices = np.where(labels == label)[0]
            group_articles = [articles[i] for i in group_indices]

            if len(group_articles) > 0:
                perspective = analyze_perspective_group(group_articles)
                perspectives.append(perspective)
                articles_by_perspective.append(group_articles)

        return perspectives, articles_by_perspective
    except Exception as e:
        print(f"Warning: Clustering failed, falling back to pairwise: {e}")
        return create_pairwise_comparison(articles, embeddings)


def create_pairwise_comparison(
    articles: List[Article], embeddings: np.ndarray
) -> Tuple[List[NarrativePerspective], List[List[Article]]]:
    """
    Create perspective groups when there are too few articles to cluster.

    Args:
        articles: List of articles
        embeddings: Pre-computed embeddings

    Returns:
        Tuple of (perspectives, articles_by_perspective)
    """
    perspectives = []
    articles_by_perspective = []
    for article in articles:
        perspectives.append(analyze_perspective_group([article]))
        articles_by_perspective.append([article])
    return perspectives, articles_by_perspective


def analyze_perspective_group(articles: List[Article]) -> NarrativePerspective:
    """
    Analyze what a narrative perspective group emphasizes.

    Args:
        articles: List of articles in the group

    Returns:
        NarrativePerspective object
    """
    # Extract focus keywords first
    focus_keywords = extract_distinctive_keywords(articles)
    
    # Get representative title - pick one that contains most focus keywords
    rep_title = select_representative_title(articles, focus_keywords)

    # Extract entities from each article
    all_entities = []
    for article in articles:
        if article.entities_json:
            try:
                entities = json.loads(article.entities_json)
                all_entities.extend([e.lower() for e in entities])
            except:
                pass

    # Get most common entities
    entity_counts = Counter(all_entities)
    key_entities = [e for e, _ in entity_counts.most_common(5)]

    # Determine sentiment using LLM (with fallback to keyword-based)
    sentiment = determine_group_sentiment_llm(articles)

    # Extract source domains (deduplicate)
    sources = []
    seen_domains = set()
    for article in articles:
        try:
            domain = extract_domain(article.source)
            if domain not in seen_domains:
                sources.append(domain)
                seen_domains.add(domain)
        except:
            if article.source not in seen_domains:
                sources.append(article.source)
                seen_domains.add(article.source)

    return NarrativePerspective(
        sources=sources,
        article_count=len(articles),
        representative_title=rep_title,
        key_entities=key_entities,
        sentiment=sentiment,
        focus_keywords=focus_keywords,
    )


def select_representative_title(articles: List[Article], focus_keywords: List[str]) -> str:
    """
    Select the most representative title for a perspective.
    
    Prioritizes titles that:
    1. Contain the most focus keywords
    2. Are descriptive (not too short)
    3. Show clear framing/perspective
    
    Args:
        articles: List of articles
        focus_keywords: Key terms this perspective emphasizes
        
    Returns:
        Representative title string
    """
    if not articles:
        return ""
    
    # Score each title
    best_title = None
    best_score = -1
    
    for article in articles:
        title_lower = article.title.lower()
        
        # Count how many focus keywords are in this title
        keyword_matches = sum(1 for kw in focus_keywords if kw in title_lower)
        
        # Prefer titles with good length (not too short or too long)
        length_score = min(len(article.title) / 100.0, 1.0)  # Normalize to 0-1
        if len(article.title) < 30:
            length_score *= 0.5  # Penalize very short titles
        
        # Combined score
        score = keyword_matches * 2 + length_score
        
        if score > best_score:
            best_score = score
            best_title = article.title
    
    # Fallback to longest title if no good match
    if best_title is None:
        best_title = max(articles, key=lambda a: len(a.title)).title
    
    return best_title


def extract_domain(source: str) -> str:
    """
    Extract clean domain from source URL or string.

    Args:
        source: Source URL or domain string

    Returns:
        Clean domain name
    """
    if source.startswith("http"):
        parsed = urlparse(source)
        domain = parsed.netloc
    else:
        domain = source

    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def extract_distinctive_keywords(articles: List[Article]) -> List[str]:
    """
    Extract distinctive keywords from article titles.

    Args:
        articles: List of articles

    Returns:
        List of distinctive keywords
    """
    # Combine all titles
    all_words = []
    for article in articles:
        title = article.title.lower()
        words = title.split()
        all_words.extend(words)

    # Remove stop words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "will",
        "would",
        "could",
        "should",
    }

    filtered_words = [w for w in all_words if w not in stop_words and len(w) > 3]

    # Get most common words
    word_counts = Counter(filtered_words)
    keywords = [w for w, _ in word_counts.most_common(5)]

    return keywords


def determine_group_sentiment_llm(articles: List[Article]) -> str:
    """
    Use LLM to accurately determine sentiment (positive/negative/neutral).
    
    Only called for political conflicts, so minimal API usage.
    
    Args:
        articles: List of articles
        
    Returns:
        'positive', 'negative', or 'neutral'
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return determine_group_sentiment(articles)  # Fallback to keyword-based
    
    try:
        client = OpenAI(api_key=openai_key)
        
        # Combine titles for analysis
        titles = "\n".join([f"- {a.title}" for a in articles[:5]])
        
        prompt = f"""Analyze the overall sentiment/tone of these news headlines:

{titles}

Is the overall tone:
- positive (celebratory, optimistic, favorable)
- negative (critical, pessimistic, unfavorable)
- neutral (factual, balanced)

Respond with ONE WORD only: positive, negative, or neutral"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model for simple task
            messages=[
                {"role": "system", "content": "You analyze news sentiment. Respond with exactly one word."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=10,
        )
        
        sentiment = response.choices[0].message.content.strip().lower()
        
        if sentiment in ['positive', 'negative', 'neutral']:
            return sentiment
        else:
            return "neutral"
            
    except Exception as e:
        print(f"LLM sentiment failed: {e}")
        return determine_group_sentiment(articles)  # Fallback


def determine_group_sentiment(articles: List[Article]) -> str:
    """
    Determine sentiment of article group using simple heuristics.

    Args:
        articles: List of articles

    Returns:
        'negative', 'neutral', or 'positive'
    """
    # Simple keyword-based sentiment
    negative_words = [
        "war",
        "attack",
        "death",
        "killed",
        "injured",
        "crisis",
        "disaster",
        "violence",
        "conflict",
        "tragedy",
    ]
    positive_words = [
        "peace",
        "victory",
        "success",
        "celebration",
        "agreement",
        "cooperation",
        "recovery",
    ]

    neg_count = 0
    pos_count = 0

    for article in articles:
        title_lower = article.title.lower()
        neg_count += sum(1 for word in negative_words if word in title_lower)
        pos_count += sum(1 for word in positive_words if word in title_lower)

    if neg_count > pos_count and neg_count > 0:
        return "negative"
    elif pos_count > neg_count and pos_count > 0:
        return "positive"
    else:
        return "neutral"


def extract_differentiating_excerpts(
    articles: List[Article],
    perspective_context: str,
    other_perspectives: List[str],
    political_leaning: Optional[str] = None,
    max_excerpts: int = 3,
) -> List[ArticleExcerpt]:
    """
    Extract key excerpts from articles that show how this perspective differs.
    
    Args:
        articles: List of articles in this perspective
        perspective_context: Description of what this perspective emphasizes
        other_perspectives: Descriptions of other perspectives for contrast
        political_leaning: Political leaning of this perspective (left/center/right)
        max_excerpts: Maximum number of excerpts to extract
        
    Returns:
        List of ArticleExcerpt objects with differentiating quotes
    """
    excerpts = []
    content_fetcher = ContentFetcher(timeout=10)
    
    # Try to fetch content for up to 5 articles (increased from 3)
    articles_to_process = articles[:min(5, len(articles))]
    
    for article in articles_to_process:
        try:
            # Fetch article content
            article_text = content_fetcher.fetch_article_text(article.url)
            
            if not article_text:
                continue
            
            # Use LLM to extract differentiating excerpts
            excerpts_from_article = extract_excerpts_with_llm(
                article=article,
                article_text=article_text,
                perspective_context=perspective_context,
                other_perspectives=other_perspectives,
                political_leaning=political_leaning,
            )
            
            excerpts.extend(excerpts_from_article)
            
            # Stop if we have enough high-quality excerpts
            if len(excerpts) >= max_excerpts:
                break
                
        except Exception as e:
            print(f"Warning: Failed to extract excerpts from {article.url}: {e}")
            continue
    
    # Return top excerpts by relevance score
    excerpts.sort(key=lambda x: x.relevance_score, reverse=True)
    return excerpts[:max_excerpts]


def extract_excerpts_with_llm(
    article: Article,
    article_text: str,
    perspective_context: str,
    other_perspectives: List[str],
    political_leaning: Optional[str] = None,
) -> List[ArticleExcerpt]:
    """
    Use LLM to identify key excerpts that show perspective differences.
    
    Args:
        article: Article object
        article_text: Full article text
        perspective_context: What this perspective emphasizes
        other_perspectives: What other perspectives emphasize
        political_leaning: Political leaning of this source (left/center/right)
        
    Returns:
        List of ArticleExcerpt objects
    """
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("Warning: OPENAI_API_KEY not set, skipping excerpt extraction")
            return []
        
        client = OpenAI(api_key=openai_key)
        
        # Prepare contrast context
        contrast_text = "\n".join([f"- {p}" for p in other_perspectives])
        
        # Truncate article text to fit in context (first ~3000 words)
        truncated_text = " ".join(article_text.split()[:3000])
        
        # Add political context if available
        political_context = ""
        if political_leaning:
            political_map = {
                "left": "liberal/progressive",
                "right": "conservative",
                "center": "centrist/neutral"
            }
            political_context = f"\n\nThis is from a {political_map.get(political_leaning, political_leaning)} source."
        
        prompt = f"""You are analyzing how different news sources frame the same event differently.

This article represents a perspective that: {perspective_context}{political_context}

Other perspectives on this event emphasize:
{contrast_text}

Article Title: {article.title}
Article Text:
{truncated_text}

Task: Extract 1-2 key excerpts (2-4 sentences each) from this article that BEST show how THIS perspective differs from others. Prioritize excerpts that show:

1. **Numerical discrepancies** - Different crowd sizes, casualty counts, or statistics
2. **Counter-narratives** - Claims that contradict other perspectives
3. **Framing differences** - Same facts described as positive/negative/neutral
4. **Ideological language** - Words revealing political stance (e.g., "freedom fighters" vs "protesters")
5. **Selective emphasis** - What this source highlights that others don't

CRITICAL: Choose excerpts that show REAL CONTRAST, not just neutral reporting. If the article mentions numbers (crowd size, attendance, costs), ALWAYS include those.

For each excerpt, provide:
1. The exact excerpt text (2-4 sentences, 150-250 words max)
2. A relevance score (0.0-1.0) indicating how well it shows the difference
3. A brief reason explaining what makes it contrasting

Return ONLY valid JSON in this exact format:
{{
  "excerpts": [
    {{
      "excerpt": "exact quote from article with full context",
      "relevance_score": 0.95,
      "contrast_reason": "Shows how this source frames the crowd size as massive while others minimize it"
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert media bias analyst who identifies the most contrasting excerpts from news articles. You understand how liberal and conservative sources frame events differently. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Convert to ArticleExcerpt objects
        excerpts = []
        for item in result.get("excerpts", []):
            excerpt = ArticleExcerpt(
                source=extract_domain(article.source),
                title=article.title,
                url=article.url,
                excerpt=item["excerpt"],
                relevance_score=item["relevance_score"],
            )
            excerpts.append(excerpt)
        
        return excerpts
        
    except Exception as e:
        print(f"Warning: LLM excerpt extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def generate_conflict_explanation(
    perspectives: List[NarrativePerspective],
    articles_by_perspective: Optional[List[List[Article]]] = None,
    force_excerpt_extraction: bool = False,
) -> ConflictExplanation:
    """
    Generate human-readable explanation of why sources conflict.

    Args:
        perspectives: List of narrative perspectives
        articles_by_perspective: Optional list of article lists for each perspective (for excerpt extraction)

    Returns:
        ConflictExplanation object
    """
    # Identify what differs
    difference_type, key_diff = identify_key_difference(perspectives)
    
    # Detect numerical discrepancies
    numeric_discrepancies = []
    if articles_by_perspective and len(articles_by_perspective) > 1:
        try:
            numeric_discrepancies = detect_numeric_discrepancies(
                perspectives, articles_by_perspective
            )
        except Exception as e:
            print(f"Warning: Failed to detect numeric discrepancies: {e}")

    # Extract excerpts if articles provided
    # Now also extracts for developing events even without major conflicts
    if articles_by_perspective and len(articles_by_perspective) == len(perspectives):
        # Always extract if forced OR if multiple perspectives exist
        should_extract = force_excerpt_extraction or len(perspectives) > 1
        
        if should_extract:
            for i, (perspective, articles) in enumerate(zip(perspectives, articles_by_perspective)):
                try:
                    # Prepare context for this perspective
                    perspective_context = f"{perspective.representative_title} (focuses on: {', '.join(perspective.focus_keywords[:3])})"
                    
                    # Prepare other perspectives for contrast
                    other_perspectives = [
                        f"{p.representative_title} (focuses on: {', '.join(p.focus_keywords[:3])})"
                        for j, p in enumerate(perspectives) if j != i
                    ]
                    
                    # Extract excerpts
                    excerpts = extract_differentiating_excerpts(
                        articles=articles,
                        perspective_context=perspective_context,
                        other_perspectives=other_perspectives,
                        political_leaning=perspective.political_leaning,
                        max_excerpts=2,
                    )
                    
                    # Convert excerpts to dicts and store
                    if excerpts:
                        perspective.representative_excerpts = [asdict(e) for e in excerpts]
                except Exception as e:
                    print(f"Warning: Failed to extract excerpts for perspective {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

    # Calculate keyword overlap between perspectives
    keyword_overlap = calculate_keyword_overlap(perspectives)
    
    # Classify the type of conflict
    classification = classify_conflict_type(perspectives, numeric_discrepancies)
    
    # Convert perspectives to dicts for JSON serialization
    perspective_dicts = [asdict(p) for p in perspectives]
    
    # Convert numeric discrepancies to dicts
    discrepancy_dicts = [asdict(d) for d in numeric_discrepancies] if numeric_discrepancies else None

    return ConflictExplanation(
        perspectives=perspective_dicts,
        key_difference=key_diff,
        difference_type=difference_type,
        numeric_discrepancies=discrepancy_dicts,
        classification=asdict(classification),
        keyword_overlap=keyword_overlap,
    )


def detect_numeric_discrepancies(
    perspectives: List[NarrativePerspective],
    articles_by_perspective: List[List[Article]],
) -> List[NumericDiscrepancy]:
    """
    Detect when different perspectives report different numbers for the same metric.
    
    Common discrepancies:
    - Crowd sizes at protests
    - Casualty counts
    - Financial figures
    - Percentages
    
    Args:
        perspectives: List of narrative perspectives
        articles_by_perspective: Articles grouped by perspective
        
    Returns:
        List of NumericDiscrepancy objects
    """
    import re
    
    discrepancies = []
    
    # Common patterns to look for
    patterns = {
        "crowd_size": [
            r"(\d+(?:,\d+)*)\s+(?:people|protesters|demonstrators|attendees|participants)",
            r"(?:crowd|turnout|attendance)\s+(?:of|reached|estimated)\s+(\d+(?:,\d+)*)",
            r"(\d+(?:,\d+)*)\s+million",
            r"(\d+(?:,\d+)*)\s+thousand",
        ],
        "casualties": [
            r"(\d+(?:,\d+)*)\s+(?:killed|dead|deaths|casualties|injured|wounded)",
            r"(?:death toll|casualties)\s+(?:of|reached)\s+(\d+(?:,\d+)*)",
        ],
        "financial": [
            r"\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|billion|trillion)?",
            r"(\d+(?:,\d+)*(?:\.\d+)?)\s+(?:dollars|USD)",
        ],
        "percentage": [
            r"(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s+percent",
        ],
    }
    
    # Extract numbers from each perspective
    perspective_numbers = {}
    
    for idx, (perspective, articles) in enumerate(zip(perspectives, articles_by_perspective)):
        numbers_by_category = {}
        
        # Check all article titles
        for article in articles:
            title_lower = article.title.lower()
            
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, title_lower, re.IGNORECASE)
                    if matches:
                        if category not in numbers_by_category:
                            numbers_by_category[category] = []
                        for match in matches:
                            # Clean the number
                            num_str = match.replace(',', '')
                            try:
                                # Try to normalize to actual value
                                if 'million' in title_lower and num_str in title_lower:
                                    num_val = float(num_str) * 1_000_000
                                elif 'thousand' in title_lower and num_str in title_lower:
                                    num_val = float(num_str) * 1_000
                                else:
                                    num_val = float(num_str)
                                numbers_by_category[category].append((num_val, match))
                            except ValueError:
                                continue
        
        perspective_numbers[idx] = numbers_by_category
    
    # Compare numbers across perspectives
    for category in patterns.keys():
        values_by_perspective = {}
        
        for idx, numbers in perspective_numbers.items():
            if category in numbers and numbers[category]:
                # Take the largest number mentioned (often most prominent)
                max_num, original_str = max(numbers[category], key=lambda x: x[0])
                values_by_perspective[idx] = {
                    "value": max_num,
                    "display": original_str,
                    "political_leaning": perspectives[idx].political_leaning,
                }
        
        # If at least 2 perspectives mention this metric, check for discrepancy
        if len(values_by_perspective) >= 2:
            values = [v["value"] for v in values_by_perspective.values()]
            max_val = max(values)
            min_val = min(values)
            
            # Check if there's significant difference
            if min_val > 0:
                ratio = max_val / min_val
                
                # Significant discrepancy if ratio > 2x
                if ratio >= 2.0:
                    # Determine significance
                    if ratio >= 10:
                        significance = "high"
                    elif ratio >= 5:
                        significance = "medium"
                    else:
                        significance = "low"
                    
                    # Create display strings
                    display_by_perspective = {}
                    for idx, data in values_by_perspective.items():
                        leaning_label = ""
                        if data["political_leaning"]:
                            leaning_map = {"left": "Liberal", "right": "Conservative", "center": "Center"}
                            leaning_label = leaning_map.get(data["political_leaning"], "")
                        
                        display_by_perspective[str(idx)] = {
                            "value": data["display"],
                            "leaning": data["political_leaning"] or "unknown",
                            "leaning_label": leaning_label,
                        }
                    
                    # Create metric label
                    metric_labels = {
                        "crowd_size": "Crowd Size / Attendance",
                        "casualties": "Casualties / Deaths",
                        "financial": "Financial Figures",
                        "percentage": "Percentages",
                    }
                    
                    discrepancy = NumericDiscrepancy(
                        metric=metric_labels.get(category, category),
                        values_by_perspective=display_by_perspective,
                        significance=significance,
                    )
                    discrepancies.append(discrepancy)
    
    return discrepancies


def calculate_keyword_overlap(perspectives: List[NarrativePerspective]) -> float:
    """
    Calculate how much perspectives' focus keywords overlap.
    
    High overlap (> 40%) = same story, different words
    Low overlap (< 40%) = genuinely different angles
    
    Args:
        perspectives: List of narrative perspectives
        
    Returns:
        Overlap ratio 0-1 (0 = no overlap, 1 = identical)
    """
    if len(perspectives) < 2:
        return 1.0
    
    # Get keyword sets for each perspective
    keyword_sets = [set(p.focus_keywords) for p in perspectives]
    
    # Calculate pairwise Jaccard similarity
    overlaps = []
    for i in range(len(keyword_sets)):
        for j in range(i + 1, len(keyword_sets)):
            intersection = keyword_sets[i] & keyword_sets[j]
            union = keyword_sets[i] | keyword_sets[j]
            
            if len(union) > 0:
                overlap = len(intersection) / len(union)
                overlaps.append(overlap)
    
    # Return average overlap
    return float(np.mean(overlaps)) if overlaps else 0.0


def classify_conflict_type(
    perspectives: List[NarrativePerspective], 
    numeric_discrepancies: List[NumericDiscrepancy]
) -> ConflictClassification:
    """
    Determine what KIND of conflict this is.
    
    Args:
        perspectives: List of narrative perspectives
        numeric_discrepancies: List of numerical differences detected
        
    Returns:
        ConflictClassification with type and confidence
    """
    # Check for numerical discrepancies
    if numeric_discrepancies:
        high_severity_nums = [d for d in numeric_discrepancies if d.significance == "high"]
        if high_severity_nums:
            return ConflictClassification(
                conflict_type="numerical",
                is_factual_dispute=True,
                is_framing_difference=False,
                confidence=0.9
            )
    
    # Check entity overlap - low overlap = factual dispute
    entity_sets = [set(p.key_entities) for p in perspectives]
    if len(entity_sets) >= 2:
        intersection = set.intersection(*entity_sets) if entity_sets else set()
        union = set.union(*entity_sets) if entity_sets else set()
        overlap = len(intersection) / len(union) if len(union) > 0 else 1.0
        
        if overlap < 0.3:
            return ConflictClassification(
                conflict_type="facts",
                is_factual_dispute=True,
                is_framing_difference=False,
                confidence=0.7
            )
    
    # Check sentiment - different sentiment = framing
    sentiments = set(p.sentiment for p in perspectives)
    if len(sentiments) > 1:
        return ConflictClassification(
            conflict_type="framing",
            is_factual_dispute=False,
            is_framing_difference=True,
            confidence=0.6
        )
    
    # Default to interpretation
    return ConflictClassification(
        conflict_type="interpretation",
        is_factual_dispute=False,
        is_framing_difference=True,
        confidence=0.5
    )


def identify_key_difference(
    perspectives: List[NarrativePerspective],
) -> Tuple[str, str]:
    """
    Determine what's different between perspective groups.

    Args:
        perspectives: List of narrative perspectives

    Returns:
        Tuple of (difference_type, description)
    """
    if len(perspectives) < 2:
        return "interpretation", "Sources provide different interpretations"

    # Check for entity differences
    all_entity_sets = [set(p.key_entities) for p in perspectives]
    if len(all_entity_sets) > 1:
        intersection = set.intersection(*all_entity_sets) if all_entity_sets else set()
        union = set.union(*all_entity_sets) if all_entity_sets else set()
        entity_overlap = len(intersection) / len(union) if len(union) > 0 else 1.0

        if entity_overlap < 0.3:
            return "facts", "Sources mention different key facts and entities"

    # Check for sentiment differences
    sentiments = [p.sentiment for p in perspectives]
    if len(set(sentiments)) > 1:
        return "framing", "Sources frame the event with different emotional tones"

    # Check for keyword differences
    all_keyword_sets = [set(p.focus_keywords) for p in perspectives]
    if len(all_keyword_sets) > 1:
        kw_intersection = (
            set.intersection(*all_keyword_sets) if all_keyword_sets else set()
        )
        kw_union = set.union(*all_keyword_sets) if all_keyword_sets else set()
        kw_overlap = len(kw_intersection) / len(kw_union) if len(kw_union) > 0 else 1.0

        if kw_overlap < 0.5:
            return (
                "emphasis",
                "Sources differ on whether to emphasize certain aspects of the story",
            )

    return "interpretation", "Sources provide different interpretations of the same facts"


